# -*- coding: utf-8 -*-
"""
Created on Sun Dec 21 11:53:00 2025

@author: Francesco
"""

import solara #Solara framework for building web apps
from model import SupplyChainModel #import of the model

from mesa.visualization import ( #Mesa modules for visualization
                                Slider,
                                SolaraViz, #special component of Solara, created by Mesa in order to link an ABM with a web interface
                                make_plot_component,
                            )

# ======================
# Cost report summary
# ======================
def get_costs(model: SupplyChainModel): #get the numbers from the model itself
    text = (
        f"### Supply Chain Costs\n\n"
        f"- **Step:** {model.steps}\n"
        f"- **Times stockout:** {model.times_stockout}\n"
        f"- **Stockout cost:** {model.stockout_cost:.2f}\n"
        f"- **Holding cost:** {model.hold:.2f}\n"        
        f"- **Transportation cost:** {model.transportation:.2f}"
    )
    return solara.Markdown(text)


# ======================
# Interactive parameters
# ======================
#the following parameters are taken by the model itself
model_params = {
    "seed": {
        "type": "InputText",
        "value": "42",
        "label": "Random Seed",
    },

    "demand_type": {
                        "type": "Select",
                        "value": "Normal",
                        "values": ["Normal", "Poisson"],
                        "label": "Demand Type",
                    },
    "order_policy": {
                        "type": "Select",
                        "value": "frp",
                        "values": ["frp", "arp", "fbr"],
                        "label": "Ordering Policy",
                    },

    "mu": Slider("Average demand (mu)", 10, 1, 50, 1),
    "sigma": Slider("Demand std (sigma)", 5, 1, 20, 1),
    "alpha": Slider("Congestion sensitivity (alpha)", 0.33, 0.0, 1.0, 0.01),
    "beta": Slider("Truck speed factor (beta)", 1.01, 0.1, 2.0, 0.01),
    "L_0": Slider("Free-flow lead time (L0)", 3, 1, 10, 1),
    "k": Slider("Safety factor (k)", 2.33, 1.0, 3.0, 0.01),
    "truck_movement": Slider("Truck movement per step", 1.5, 0.1, 5.0, 0.1),
    "p": Slider("Unit stockout penalty (p)", 1.0, 0.0, 10.0, 0.1),
    "h": Slider("Unit holding cost (h)", 0.01, 0.0, 1.0, 0.01),
    "c": Slider("Unit transport cost (c)", 0.01, 0.0, 1.0, 0.01),
    "n_trucks": Slider("Number of trucks", 8, 1, 20, 1),
}


# ======================
# Cost plot
# ======================

def post_process_lines(ax):
    # figure dimension
    ax.figure.set_size_inches(12, 9) 

    # axis titles
    ax.set_xlabel("Steps", fontsize=16)
    ax.set_ylabel("Cost", fontsize=16)
    
    # Ticks axes
    ax.tick_params(axis='x', labelsize=12)
    ax.tick_params(axis='y', labelsize=12)
    
    #change lines thickness
    for line in ax.lines:
        line.set_linewidth(3)

    #legend
    leg = ax.legend(loc="center left", bbox_to_anchor=(1, 0.92), fontsize=12, 
                    title="Cost Types", title_fontsize=12)

CostPlot = make_plot_component(
    {
        "hold": "blue",
        "stockout_cost": "red",
        "transportation": "orange",
    },
    backend="matplotlib", #graphic library used in backend
    post_process = post_process_lines
)



# ======================
# Model & visualization
# ======================

page = SolaraViz(
    SupplyChainModel(),
    components=[
        CostPlot,
        get_costs,
    ],

    model_params=model_params,
    name="Supply Chain Model",
)


page