# -*- coding: utf-8 -*-
"""
Created on Sat Dec 20 08:59:13 2025

@author: Francesco
"""

"""
Pure agent based approach script.
Keep in mind that the script 'ABM.py' instead is a procedural simulation, with
a central logic based on agents acting as passive structures.
Now in this script the time progresses with 'step()', the model coordinates, 
does not decide everything.
Each behaviour must stay within the agent that does it.

Agent Based Modeling script for:
            'Risk-Aware Inventory Management Through Agent-Based Simulation
            Analyzing Reorder Policies Under Demand and Queue Uncertainty'

the agents are:
    • Trucks, moving stocks;
    • Factory, generating stocks;
    • Customers, final firms requiring stocks based on the endogenous final 
      clients demand;
      
through the script there are many 'N.B.:' to check with a simple 'ctrl+f'
"""
import mesa #Python agent based modeling library
import numpy as np
from numpy import random #for Normal and Poisson distribution of demand

#TODO! CHECK THAT THE MATH STICKS TO THE MODEL DEFINED IN THE ARTICLE


#global hyperparameters that must be set
temporal_horizon = 365 #e.g.: 30 days for finishing ONE simulation episode
demand_type = "Normal" #what kind of PDF we use to generate the demand
#fundamental hyperparameters of the model
mu = 10 #average demand per simulation_step
sigma = 5 #standard deviation of demand
alpha = 0.33 #congestion sensitivity coefficient
beta = 1.01 #how faster the unloaded truck moves with respect to the loaded ones
L_0 = 3 #free-flow lead time for delivering and picking-up stocks
k = 2.33 #safety factor [1.28; 1.65; 2.33]
kernel_size = 3 #for calculating the moving averages
truck_movement = 1.5 #how much the truck moves at each simulation step
#cost hyperparameters
p = 1 #unit stockout penalty
h = 0.01 #unit holding cost
c = 0.01 #unit transport cost


#general global functions used by the agents
def demand_generator(mu, sigma):
    if demand_type == "Normal":
        demand = random.normal(loc=mu, scale=sigma)
    else:
        demand = random.poisson(lam=mu)
    return max(0, round(demand)) #make it integer and always non-negative

def lead_time_updater(traffic):
    L = L_0 + alpha*traffic
    return round(L)


class Factory(mesa.Agent):
    """An agent that produces a stochastic amount of goods per day"""
    
    def __init__(self, model, warehouse):
        #pass the parameters of the parent class
        super().__init__(model)
        
        self.warehouse = warehouse #number of stocks in the warehouse
        #since we do not model any queue upstream, this class is super easy
    
    def step(self):
        self.warehouse += mu  #average production
        
class Truck(mesa.Agent):
    """An agent that delivers goods between factory and customer"""
    
    def __init__(self,  model, maximum_load, available, position, current_load, state):
        #pass the parameters of the parent class
        super().__init__(model)
        
        self.maximum_load = maximum_load #maximum number of stocks that can be
                                        #carried
        self.available = available #whether it is available for transportation
        self.position = position #where the truck is (close (i.e.: 0) or far 
                                 #way for delivery)
        self.current_load = current_load #the amount of stock is currenlty bringing
        self.state = state #'idle', 'going', 'returning'
        
    def assign_load(self, quantity):
        self.current_load = quantity
        self.available = False
        self.state = "going" #the truck is moving from: arinox to: 
                                                                #thales

    def step(self):
        # ===== ARINOX -> THALES =====
        if self.state == "going":
            self.position += truck_movement
            
            #update the traffic
            traffic = sum(not t.available for t in self.model.trucks)
            L = lead_time_updater(traffic)

            if self.position >= L:
                #arrival and unload
                customer = self.model.customer
                customer.warehouse += self.current_load
                self.model.costs["transportation"] += c * self.current_load
                self.current_load = 0
                #change the state
                self.state = "returning"
                self.position = L

        # ===== THALES -> ARINOX =====
        elif self.state == "returning":
            self.position -= beta * truck_movement

            if self.position <= 0:
                self.position = 0
                self.available = True
                self.state = "idle"
        
class Customer(mesa.Agent):
    """An agent that requires a stochastic amount of goods based on external
        exogenous demands"""
        
    def __init__(self, model, warehouse, demand_history, orders_status):
        #pass the parameters of the parent class
        super().__init__(model)
        
        self.warehouse = warehouse #number of stocks in the warehouse
        self.demand_history = demand_history #in order to draw statistics  
        self.orders_status = orders_status #status of all orders
    
    def frp(self, Q=mu): #decided fixed quantity to order (hyperparameter)        
        ROP = mu*L_0 + k*sigma #*math.sqrt(L)
        
        if self.warehouse <= ROP:
            return Q
    
    def arp(self, Q=mu, n=kernel_size): #decided fixed quantity to rder 
                    #(hyperparameter), n indicates the convolution kernel size   
        SS = k*sigma
        weights = np.ones(n)/n #weights of the kernel
        #we only take the last number of the moving average and we round into 
        #integer, 'valid' means no padding
        D = round((np.convolve(self.demand_history, weights, mode='valid'))[-1])
        ROP = D + SS
        
        if self.warehouse <= ROP:
            return Q
    
    def fbr(self, n=kernel_size): #here both D and Q are calculated though 
                      #moving averages, n indicates the convolution kernel size
        SS = k*sigma
        weights = np.ones(n)/n #weights of the kernel
        #we only take the last number of the moving average and we round into 
        #integer, 'valid' means no padding
        D = round((np.convolve(self.demand_history, weights, mode='valid'))[-1])        
        ROP = D + SS        
        Q = D
        
        if self.warehouse <= ROP:
            return round(Q)
    
    def place_order(self, quantity):
        factory = self.model.factory
        
        #if the factory has enough warehouse
        if factory.warehouse < quantity:
            return #we stop immmediately the exacution of the function without returning any value
        
        #we try to find an available truck to send the stocks
        for truck in self.model.trucks:
            #if a truck is available
            if truck.available and quantity <= truck.maximum_load:
                truck.assign_load(quantity)
                factory.warehouse -= quantity #we are using stocks from 
                                                    #the warehouse
                break #since the truck has been found we exit the for loop
    
    def step(self):
        # exogenous demand generated
        demand = demand_generator(mu, sigma)
        self.demand_history.append(demand) #for computing moving averages

        #if the warehouse of the Customer is not enough
        if self.warehouse < demand:
            #counter of the number of times we stockout
            self.model.costs["times_stockout"] += 1
            #in this case we must update the cost due to the stockout
            self.model.costs["stockout_cost"] += p * (demand - self.warehouse)
            #we generate a delay, with the gravity of the current demand (stock-out)
            self.orders_status[self.model.steps] = demand
            #in any case we sell what we have, hence we empty the warehouse
            self.warehouse = 0
        #if the warehouse of the Customer is enough 
        else:
            #we sell the required amount of stock
            self.warehouse -= demand 

        #we generate the demand, once the warehouse has been changed
        #N.B.: from here change the chosen policy
        order = self.frp()

        #if the Customer made an order and the factory is not empty we try to 
        #find a truck available
        if order is not None:
            self.place_order(order)

    
class SupplyChainModel(mesa.Model):
    """A model for interacting: Factory, Trucks and Customer"""
    
    def __init__(self, seed=None):
        super().__init__(seed=seed) #reproducibility of the results
        
        #dictionary containing the results of the simulation
        self.costs = {
            "times_stockout": 0,
            "stockout_cost": 0,
            "hold": 0,
            "transportation": 0,
        }
        
        #now we create the agents
        self.factory = Factory.create_agents(
            model = self,
            n = 1,
            warehouse = 5
        )[0] #we extract the single factory agent inside the list

        self.trucks = Truck.create_agents(
            model = self,
            n = 8,
            #N.B.: if you want different hyperparameters for each agent, 
            #create a list, mesa will automatically join index by index
            maximum_load = [20, 25, 15, 50, 50, 100, 25, 50], 
            available = True,
            position = 0,
            current_load = 0,
            state = "idle"
        )

        self.customer = Customer.create_agents(
            model=self,
            n=1,
            warehouse = mu + sigma*k,
            demand_history = [[]], #we are dealing with a list of 
                    #agents, so first thing first is to unpack the first list
            orders_status = [{}]
        )[0] #we extract the single customer agent inside the list
        
        
    def step(self):
        """Advance the model by one step.
        The iteration order is deterministic, based on the order of creation
        of the agents: Factory -> Trucks -> Customer, they will be always 
        called in this order for each step
        
        1. Factory.step()
        2. Truck(s).step()
        5. Customer.step()
        6. holding cost (in the Model)     
        
        """
        self.agents.do("step") #for all the agents we call their "step()" methods
        
        #updating the holding cost
        self.costs["hold"] += h * self.customer.warehouse
        
        
#run the model
model = SupplyChainModel(seed=42) #model creation

for _ in range(temporal_horizon): #run
    model.step()

print(model.costs)
        
        
        
        
    

        
        
        
        
        
        