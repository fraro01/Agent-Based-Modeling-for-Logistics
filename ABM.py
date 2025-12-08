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
      clients deman;

"""

import numpy as np
from numpy import random #for Normal and Poisson distribution of demand

#global hyperparameters that must be set
temporal_horizon = 365 #e.g.: 30 days for finishing ONE simulation episode
simulation_step = 1 #e.g.: 1 day for updating the states within the episode
demand_type = "Normal" #what kind of PDF we use to generate the demand
#fundamental hyperparameters of the model
mu = 10 #average demand per simulation_step
sigma = 1 #standard deviation of demand
alpha = 0.33 #congestion sensitivity coefficient
L_0 = 3 #free-flow lead time for delivering and picking-up stocks
k = 1.28 #safety factor
#cost hyperparameters
p = 1 #unit stockout penalty
h = 0.01 #unit holding cost
c = 0.01 #unit transport cost

class Factory:
    def __init__(self, warehouse, production_lead_time, production_state):
        self.warehouse = warehouse #number of stocks in the warehouse
        
class Truck:
    def __init__(self,  maximum_load, available, position, current_load):
        self.maximum_load = maximum_load #maximum number of stocks that can be
                                        #carried
        self.available = available #whether it is available for transportation
        self.position = position #where the truck is (close of far way for delivery)
        self.current_load = current_load #the amount of stock is currenlty bringing
        
class Customer:
    def __init__(self, warehouse, demand_history, orders_status):
        self.warehouse = warehouse #number of stocks in the warehouse
        self.demand_history = demand_history #in order to draw statistics  
        self.orders_status = orders_status #status of all orders
    
    def frp(self, Q=7): #decided fixed safety stock and quantity to order
                              #(they are hyperparameters)        
        ROP = mu*L_0 + k*sigma
        
        if self.warehouse <= ROP:
            return Q
    
    
    def arp(self, Q=7, n=3): #decided fixed quantity to rder (hyperparameter)
                             #n indicates the convolution kernel size   
        SS = k*sigma
        weights = np.ones(n)/n #weights of the kernel
        #we only take the last number of the moving average and we round into 
        #integer, 'valid' means no padding
        D = round((np.convolve(self.demand_history, weights, mode='valid'))[-1])
        ROP = D + SS
        
        if self.warehouse <= ROP:
            return Q
    
    
    def fbr(self, n=3): #here both D and Q are calculated though moving averages
                        #n indicates the convolution kernel size
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
step_counter = 0
truck_movement = 1.5 #how much the truck moves at each simulation step
arinox = Factory(warehouse=5,
                 production_lead_time=0.08,
                 production_state=0)
thales = Customer(warehouse=11,
                  demand_history=[],
                  orders_status={})
truck1 = Truck(maximum_load=20, 
               available=True, 
               position=0,
               current_load=0)
truck2 = Truck(maximum_load=25, 
               available=True, 
               position=0, 
               current_load=0)
truck3 = Truck(maximum_load=15, 
               available=True, 
               position=0, 
               current_load=0)
truck4 = Truck(maximum_load=56, 
               available=True, 
               position=0, 
               current_load=0)
truck5 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0)
truck6 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0)
truck7 = Truck(maximum_load=200, 
               available=True, 
               position=0, 
               current_load=0)
lista_trucks = [truck1, truck2, truck3,
                truck4, 
                #truck5,
                #truck6,
                #truck7
                ]
costs = {"times_stockout":0,
         "stockout_cost":0, 
         "hold":0,
         "transportation":0
         }
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
        
    #if the warehouse of the Customer is enough           
    elif thales.warehouse >= external_demand:
        thales.warehouse -= external_demand #we sell the required amount of stock
               
    #we generate the demand, once the warehouse has been changed
    customer_demand = thales.frb()
    
    #if the Customer made an order and the factory is not empty we try to 
    #find a truck available
    if (customer_demand is not None) and arinox.warehouse >= customer_demand:
        #we try to find an available truck to send the stocks
        for truck in lista_trucks:
            #if a truck is available
            if truck.available == True and customer_demand <= truck.maximum_load:
                truck.current_load = customer_demand
                truck.available = False #we turn it to unavailable
                arinox.warehouse -= customer_demand #we are using stocks from the warehouse
                break #since the truck has been found we exit the for loop
            
    #normal production for the Factory, normally produces per simulation_step
    #the average demand per simulation_step
    arinox.warehouse += mu
    
    #update the traffic
    traffic = 0
    for truck in lista_trucks:
        if truck.available == False: #it means the truck is on the road
           traffic += 1
    traffic = traffic #otherwise adjust alpha ad divide it by: len(lista_trucks)
   
    L = lead_time_updater(traffic)
    
    for truck in lista_trucks:
        if truck.position >= L: #if the truck has arrived at the Customer
            thales.warehouse += truck.current_load
            costs["transportation"] += c*truck.current_load
            truck.current_load = 0
            truck.available = True
            truck.position = 0 #we set the position of the truck back to zero
            
            
        if truck.position < L and truck.available == False:
            truck.position += truck_movement
            
    
    #updating the holding cost
    costs["hold"] += h*thales.warehouse
    
    step_counter += simulation_step #final counter
