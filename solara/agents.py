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
# ======================        global variable
def demand_generator(mu, sigma, demand_type):
    if demand_type == "Normal":
        demand = random.normal(loc=mu, scale=sigma)
    else:
        demand = random.poisson(lam=mu)
    return max(0, round(demand)) #make it integer and always non-negative

def lead_time_updater(model, traffic):
    #TODO! see the maths in the paper
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
        self.warehouse += self.model.mu #average production per step


class Truck(mesa.Agent):
    """An agent that delivers goods between factory and customer"""
    
    def __init__(self,  model, available, position, current_load, state):
        #pass the parameters of the parent class
        super().__init__(model)
        self.available = available #whether it is available for transportation
        self.position = position #where the truck is (close (i.e.: 0) or far 
                                 #way for delivery)
        self.current_load = current_load #the amount of stock is currenlty bringing
        self.state = state #'idle', 'going', 'returning'
    
    #loading the truck
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

            #if we have already reached the customer
            if self.position >= L:
                #arrival and unload
                customer = self.model.customer
                customer.warehouse += self.current_load
                # transportation cost update
                self.model.transportation += self.model.c * self.current_load
                #unload the truck
                self.current_load = 0
                #change the state
                self.state = "returning"
                self.position = L

        # ===== THALES -> ARINOX =====
        elif self.state == "returning":
            #moving the truck back
            self.position -= self.model.beta * self.model.truck_movement

            #if we have already reached the factory
            if self.position <= 0:
                self.position = 0
                self.available = True
                self.state = "idle"


class Customer(mesa.Agent):
    """An agent that requires a stochastic amount of goods based on external
        exogenous demands"""
        
    def __init__(self, model, warehouse, demand_history):
        #pass the parameters of the parent class
        super().__init__(model)
        
        self.warehouse = warehouse #number of stocks in the warehouse
        self.demand_history = demand_history #in order to draw statistics
        
    #TODO! for all of them adjust them accordingly to the paper
    def frp(self): #decided fixed quantity to order (hyperparameter)    
        Q = self.model.mu    
        ROP = self.model.mu*self.model.L_0 + self.model.k*self.model.sigma
        
        if self.warehouse <= ROP:
            return Q
    
    def arp(self): #decided fixed quantity to reoder 
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
        
        #if the factory has not enough warehouse
        if factory.warehouse < quantity:
            return #we stop immmediately the execution of the function without returning any value
        
        #we try to find an available truck to send the stocks
        for truck in self.model.trucks:
            #if a truck is available
            if truck.available:
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
            #update the cost of stock-out
            self.model.stockout_cost += self.model.p * (demand - self.warehouse)
            #in any case we sell what we have, hence we empty the warehouse
            self.warehouse = 0
        #if the warehouse of the Customer is enough 
        else:
            #we sell the required amount of stock
            self.warehouse -= demand 

        #we generate the demand, once the warehouse has been changed
        #from here change the chosen policy
        if self.model.order_policy == "FRP":
            order = self.frp()
        elif self.model.order_policy == "ARP":
            order = self.arp()
        else: #FBR
            order = self.fbr()

        #if the Customer made an order and the factory is not empty we try to 
        #find a truck available
        if order is not None:
            self.place_order(order)