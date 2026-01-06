# -*- coding: utf-8 -*-
"""
Created on Sun Dec 21 11:48:00 2025

@author: Francesco
"""

import mesa #Python agent based modeling library
import numpy as np #numerical computing library
from agents import (Factory, # import of the agents
                    Customer, 
                    Truck,
                    lead_time_updater) #for lead time calculation kpi

# ======================
# Model
# ======================
class SupplyChainModel(mesa.Model):
    """A model for interacting: Factory, Trucks and Customer"""
    
    def __init__(
        self,
        seed=None, #reproducibility
        order_policy = "FRP", #ordering policy: FRP, ARP, FBR
        demand_type = "Normal", #what kind of PDF we use to generate the demand
        #fundamental hyperparameters of the model
        mu = 10, #average demand per simulation_step
        sigma = 5, #standard deviation of demand
        alpha = 0.75, #congestion sensitivity coefficient
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
    ):
        #pass the parameters of the parent class
        super().__init__(seed=seed)
        
        #save the parameers of the model, so that they are accessible by the agents
        self.order_policy = order_policy
        self.demand_type = demand_type
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
       
        #performance variables for DataCollector    
        self.hold = 0.0
        self.stockout_cost = 0.0
        self.times_stockout = 0
        self.transportation = 0.0
        #added for kpis
        self.lead_time = 0
        self.customer_warehouse_history = []
        self.traffic_history = []
        self.lead_time_history = []


        # ---- Agents ----        
        self.factory = Factory(model = self, 
                               warehouse = 5,
                               )
        
        self.customer = Customer(model = self, 
                                 warehouse = mu + sigma * k, 
                                 demand_history = [],
                                 )

        # Trucks: create a list of agents, one per truck
        self.trucks = []
        for i in range(n_trucks):
            truck = Truck(
                model=self,
                available=True,
                position=0,
                current_load=0,
                state="idle",
            )
            self.trucks.append(truck)
        
        #register all the agents
        for agent in [self.factory, self.customer, *self.trucks]:
            self.agents.add(agent)

        #directly linked and updated by the performance variables
        self.datacollector = mesa.DataCollector(
            model_reporters = {"holding": "hold",
                               "stockout": "stockout_cost",
                               "times_stockout": "times_stockout",
                               "transportation": "transportation",
                               #added for kpis
                               "lead_time": "lead_time",
                               "customer_warehouse_history": "customer_warehouse_history",
                               "traffic_history": "traffic_history",
                               "lead_time_history" : "lead_time_history",
                               
                               }
        )
        
    def step(self):

        # agents act
        self.agents.do("step")
    
        # update holding cost
        self.hold += self.h * self.customer.warehouse
    
        # collect kpis data
        self.customer_warehouse_history.append(self.customer.warehouse)
        traffic = (sum(not t.available for t in self.trucks) / len(self.trucks))
        lead_time = lead_time_updater(self, traffic)
        self.traffic_history.append(traffic)
        self.lead_time_history.append(lead_time)
        self.lead_time = lead_time

        # collect data at the end of the step
        self.datacollector.collect(self)

    def compute_kpis(self):
        """Compute additional KPIs after the simulation ends"""
        #lead time avg and coefficient of variation
        AVG_L = float(np.mean(self.lead_time_history)) if len(self.lead_time_history) > 0 else 0
        CV_L = float(np.std(self.lead_time_history) / AVG_L) if AVG_L > 0 else 0
        #warehouse avg and coefficient of variation
        AVG_S = float(np.mean(self.customer_warehouse_history)) if len(self.customer_warehouse_history) > 0 else 0
        CV_S = float(np.std(self.customer_warehouse_history) / AVG_S) if AVG_S > 0 else 0
        #traffic avg
        AVG_T = float(np.mean(self.traffic_history)) if len(self.traffic_history) > 0 else 0

        return {
            "avg_lead_time": AVG_L,
            "cv_lead_time": CV_L,
            "cv_inventory": CV_S,
            "avg_traffic": AVG_T * 100,
        }