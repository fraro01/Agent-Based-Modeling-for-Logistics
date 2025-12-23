# -*- coding: utf-8 -*-
"""
Created on Sun Dec  7 12:07:53 2025

@author: Francesco
"""

"""
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

import numpy as np
from numpy import random #for Normal and Poisson distribution of demand
import math #for and easier sqrt
#TODO! CHECK THAT THE MATH STICKS TO THE MODEL DEFINED IN THE ARTICLE

#global hyperparameters that must be set
temporal_horizon = 365 #e.g.: 30 days for finishing ONE simulation episode
simulation_step = 1 #e.g.: 1 day for updating the states within the episode
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

class Factory:
    def __init__(self, warehouse):
        self.warehouse = warehouse #number of stocks in the warehouse
        #since we do not model any queue upstream, this class is super easy
        
class Truck:
    def __init__(self,  maximum_load, available, position, current_load, state):
        self.maximum_load = maximum_load #maximum number of stocks that can be
                                        #carried
        self.available = available #whether it is available for transportation
        self.position = position #where the truck is (close (i.e.: 0) or far 
                                 #way for delivery)
        self.current_load = current_load #the amount of stock is currenlty bringing
        self.state = state #'idle', 'going', 'returning'
        
class Customer:
    def __init__(self, warehouse, demand_history, orders_status):
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
        
def demand_generator(mu, sigma):
    if demand_type == "Normal":
        demand = random.normal(loc=mu, scale=sigma)
    else:
        demand = random.poisson(lam=mu)
    return max(0, round(demand)) #make it integer and always non-negative

def lead_time_updater(traffic):
    L = L_0 + alpha*traffic
    return round(L)



#initilization of the simulation
#N.B.: the initialization is fundamental, like initial conditions in PDE
arinox = Factory(warehouse=5
                 )
thales = Customer(warehouse=mu + sigma*k,
                  demand_history=[],
                  orders_status={})
truck1 = Truck(maximum_load=20, 
               available=True, 
               position=0,
               current_load=0,
               state = "idle")
truck2 = Truck(maximum_load=25, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
truck3 = Truck(maximum_load=15, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
truck4 = Truck(maximum_load=56, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
truck5 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
truck6 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
truck7 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
truck8 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
truck9 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
truck10 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
truck11 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
truck12 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
truck13 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0,
               state = "idle")
#N.B.: from here we could change the number of trucks we could use, even with
#varying cargo capacity
lista_trucks = [truck1, truck2, truck3,
                truck4, 
                truck5,
                truck6,
                truck7,
                truck8,
                #truck9,
                #truck10,
                #truck11,
                #truck12,
                #truck13,
                ]
#dictionary containing the results of the simulation
costs = {"times_stockout":0,
         "stockout_cost":0, 
         "hold":0,
         "transportation":0
         }
#simulation model
step_counter = 0
#N.B.: in order to replicate always the same results
np.random.seed(42)
while step_counter < temporal_horizon:
    
    #we generate the demand for the current iteration
    external_demand = demand_generator(mu, sigma)
    thales.demand_history.append(external_demand) #for computing Moving Average
          
    #if the warehouse of the Customer is not enough
    if thales.warehouse < external_demand:
        #we generate a delay, with the gravity of the current demand (stock-out)
        thales.orders_status[str(step_counter)] = external_demand
        #in this case we must update the cost due to the stockout
        costs["stockout_cost"] += p*(external_demand-thales.warehouse)
        costs["times_stockout"] += 1 #counter of the number of times we stockout
        #in any case we sell what we have, hence we empty the warehouse
        thales.warehouse = 0
        
    #if the warehouse of the Customer is enough           
    elif thales.warehouse >= external_demand:
        thales.warehouse -= external_demand #we sell the required amount of stock
               
    #we generate the demand, once the warehouse has been changed
    #N.B.: from here change the chosen policy
    #L = lead_time_updater(sum(1 for truck in lista_trucks if not truck.available))
    customer_demand = thales.frp()
    
    #if the Customer made an order and the factory is not empty we try to 
    #find a truck available
    if (customer_demand is not None) and arinox.warehouse >= customer_demand:
        #we try to find an available truck to send the stocks
        for truck in lista_trucks:
            #if a truck is available
            if truck.available == True and customer_demand <= truck.maximum_load:
                truck.current_load = customer_demand
                truck.available = False #we turn it to unavailable
                truck.state = 'going' #the truck is moving from: arinox to: 
                                                                        #thales
                arinox.warehouse -= customer_demand #we are using stocks from 
                                                    #the warehouse
                break #since the truck has been found we exit the for loop
            
    #normal production for the Factory, normally produces per simulation_step
    #the average demand per simulation_step
    #N.B.: we could try to set it stochastic, maybe even with a Weibull to 
    #simulate failures
    arinox.warehouse += mu
    
    #update the traffic
    traffic = 0
    for truck in lista_trucks:
        if truck.available == False: #it means the truck is on the road
           traffic += 1 #otherwise adjust alpha ad divide it by: len(lista_trucks) 
    L = lead_time_updater(traffic)
    
    #update the state of the trucks
    for truck in lista_trucks:
        # ===== ARINOX -> THALES =====
        if truck.state == "going":
            truck.position += truck_movement
    
            if truck.position >= L:
                # arrival and unload
                thales.warehouse += truck.current_load
                costs["transportation"] += c * truck.current_load
                truck.current_load = 0
                # change the state
                truck.state = "returning"
                truck.position = L
    
        # ===== THALES -> ARINOX =====
        elif truck.state == "returning":
            truck.position -= beta*truck_movement
    
            if truck.position <= 0:
                truck.position = 0
                truck.state = "idle"
                truck.available = True
                       

            
    #updating the holding cost
    costs["hold"] += h*thales.warehouse
    
    step_counter += simulation_step #final counter