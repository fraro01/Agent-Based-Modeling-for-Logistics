# -*- coding: utf-8 -*-
"""
Created on Sun Dec 21 11:47:58 2025

@author: Francesco
"""

import mesa #Python agent based modeling library
import numpy as np #for numerical computations
from numpy import random #for Normal and Poisson distribution of demand

# ======================
# Utility functions
# ======================
def demand_generator(mu, sigma, demand_type):
    if demand_type == "Normal":
        demand = random.normal(loc=mu, scale=sigma)
    else:
        demand = random.poisson(lam=mu)
    return max(0, round(demand)) #make it integer and always non-negative

def lead_time_updater(model, traffic):
    L = model.L_0 + model.alpha*traffic
    return round(L)

# ======================
# Agents
# ======================
class Factory(mesa.Agent):
    """An agent that produces a stochastic amount of goods per day"""
    
    def __init__(self, model, warehouse):
        #pass the parameters of the parent class
        super().__init__(model)
        self.warehouse = warehouse #number of stocks in the warehouse
        #since we do not model any queue upstream, this class is super easy
        
    def step(self):
        self.warehouse += self.model.mu #average production


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
            self.position += self.model.truck_movement
            
            #update the traffic
            traffic = sum(not t.available for t in self.model.trucks)
            L = lead_time_updater(self.model, traffic)

            if self.position >= L:
                #arrival and unload
                customer = self.model.customer
                customer.warehouse += self.current_load
                # Truck.step
                self.model.transportation += self.model.c * self.current_load
                self.current_load = 0
                #change the state
                self.state = "returning"
                self.position = L

        # ===== THALES -> ARINOX =====
        elif self.state == "returning":
            self.position -= self.model.beta * self.model.truck_movement

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
        
    def frp(self): #decided fixed quantity to order (hyperparameter)    
        Q = self.model.mu    
        ROP = self.model.mu*self.model.L_0 + self.model.k*self.model.sigma #*math.sqrt(L)
        
        if self.warehouse <= ROP:
            return Q
    
    def arp(self): #decided fixed quantity to rder 
                    #(hyperparameter), n indicates the convolution kernel size 
        Q = self.model.mu
        n = self.model.kernel_size
        SS = self.model.k*self.model.sigma
        weights = np.ones(n)/n #weights of the kernel
        #we only take the last number of the moving average and we round into 
        #integer, 'valid' means no padding
        D = round((np.convolve(self.demand_history, weights, mode='valid'))[-1])
        ROP = D + SS
        
        if self.warehouse <= ROP:
            return Q
    
    def fbr(self): #here both D and Q are calculated though 
                      #moving averages, n indicates the convolution kernel size
        n = self.model.kernel_size
        SS = self.model.k*self.model.sigma
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
        demand = demand_generator(self.model.mu, self.model.sigma, self.model.demand_type)
        self.demand_history.append(demand) #for computing moving averages

        #if the warehouse of the Customer is not enough
        if self.warehouse < demand:
            #counter of the number of times we stockout
            self.model.times_stockout += 1
            self.model.stockout_cost += self.model.p * (demand - self.warehouse)
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
        if self.model.order_policy == "frp":
            order = self.frp()
        elif self.model.order_policy == "arp":
            order = self.arp()
        else: #fbr
            order = self.fbr()

        #if the Customer made an order and the factory is not empty we try to 
        #find a truck available
        if order is not None:
            self.place_order(order)



