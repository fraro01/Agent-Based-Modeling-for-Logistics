# -*- coding: utf-8 -*-
"""
Created on Sun Dec 21 11:48:00 2025

@author: Francesco
"""

import mesa
import networkx as nx
from mesa.space import NetworkGrid
from agents import (Factory, 
                    Customer, 
                    Truck)

# ======================
# Model
# ======================
class SupplyChainModel(mesa.Model):
    """A model for interacting: Factory, Trucks and Customer"""
    
    def __init__(
        self,
        seed=None, #reproducibility
        order_policy = "frp", #ordering policy: frp, arp, fbr
        demand_type = "Normal", #what kind of PDF we use to generate the demand
        #fundamental hyperparameters of the model
        mu = 10, #average demand per simulation_step
        sigma = 5, #standard deviation of demand
        alpha = 0.33, #congestion sensitivity coefficient
        beta = 1.01, #how faster the unloaded truck moves with respect to the loaded ones
        L_0 = 3, #free-flow lead time for delivering and picking-up stocks
        k = 2.33, #safety factor [1.28; 1.65; 2.33]
        kernel_size = 3, #for calculating the moving averages
        truck_movement = 1.5, #how much the truck moves at each simulation step
        #cost hyperparameters
        p = 1, #unit stockout penalty
        h = 0.01, #unit holding cost
        c = 0.01, #unit transport cost
        n_trucks=8,#number of trucks initial
        truck_loads=(20, 25, 15, 50, 50, 100, 25, 50)
        
    ):
        #pass the parameters of the parent class
        super().__init__(seed=seed)
        
        #save the parameers of the model, so that they are accessible by the agents
        self.demand_type = demand_type
        self.order_policy = order_policy
        self.mu = mu
        self.sigma = sigma
        self.alpha = alpha
        self.beta = beta
        self.L_0 = L_0
        self.k = k
        self.kernel_size = kernel_size
        self.truck_movement = truck_movement
        self.p = p
        self.h = h
        self.c = c
       
        #performance variables      
        self.hold = 0.0
        self.stockout_cost = 0.0
        self.times_stockout = 0
        self.transportation = 0.0
        self.steps = 0  # for visualizing and Customer.orders_status

        # ---- Agents ----        
        self.factory = Factory(model = self, 
                               warehouse = 5,
                               )
        
        self.customer = Customer(model = self, 
                                 warehouse = mu + sigma * k, 
                                 demand_history = [],
                                 orders_status = {},
                                 )

        # Trucks: create a list of agents, one per truck
        self.trucks = []
        for i in range(n_trucks):
            truck = Truck(
                model=self,
                maximum_load=50, #fixed!!!
                available=True,
                position=0,
                current_load=0,
                state="idle",
            )
            self.trucks.append(truck)
        
        #register all the agents
        for agent in [self.factory, self.customer, *self.trucks]:
            self.agents.add(agent)

        
        self.datacollector = mesa.DataCollector(
            model_reporters = {"hold": "hold",
                               "stockout_cost": "stockout_cost",
                               "times_stockout": "times_stockout",
                               "transportation": "transportation"}
        )
        


    def step(self):
        # increment step counter FIRST
        self.steps += 1
    
        # agents act
        self.agents.do("step")
    
        # update holding cost
        self.hold += self.h * self.customer.warehouse
    
        # collect data
        self.datacollector.collect(self)

