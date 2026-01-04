# -*- coding: utf-8 -*-
"""
Created on Sun Dec 21 11:53:00 2025

@author: Francesco
"""

import solara #Solara framework for building web apps
from model import SupplyChainModel #import of the model

from mesa.visualization import ( #Mesa modules for visualization
                                Slider, #to create sliders for parameters
                                SolaraViz, #special component of Solara, created by Mesa in order to link an ABM with a web interface
                                make_plot_component, #to create plots
                            )

# ===============================
# Cost report summary & Info
# ===============================
def get_costs(model: SupplyChainModel):
    text = (
        f"### Supply Chain Costs\n"
        f"- **Step:** {model.steps}\n"
        f"- **Times stockout:** {model.times_stockout}\n"
        f"- **Stockout cost:** {model.stockout_cost:.2f}\n"
        f"- **Holding cost:** {model.hold:.2f}\n"        
        f"- **Transportation cost:** {model.transportation:.2f}"
    )

    return solara.Markdown(
        text,
        style={
        }
    )
def model_info(model: SupplyChainModel):
    text_info = (
        f"**Info**  \n"
        f"The model is composed of a total of {len(model.agents)} agents: one *factory agent*, responsible for producing inventory, "
        f"one *customer agent*, responsible for purchasiong and holding stock, and the rest are *truck agents* that enable the "
        f"transportation of goods between the factory and the customer.\n"
        f"The panel on the left allows to tweak the model hyperparameters in order to explore different scenarios. "
        f"The most relevant is the *Ordering policy*, which determines the inventory replenishmnet strategy adopted by the customer.\n"
        f"The plot shows the evolution of the different cost components over time, while the panel on the right provides a numerical summary.  \n"
        f"*Times stockout:* number of occurerences the customer ran out of stock during the simulation.\n"
        f"*Stockout cost:* cumulative cost incurred due to stockouts.\n"
        f"*Holding cost:* cumulative cost of holding inventory.\n"
        f"*Transportation cost:* cumulative cost of transporting goods.\n"
    )

    return solara.Markdown(
        text_info,
        style={
            "padding-top": "5%",
            "font-size": "60%",
            "line-height": "1.2",
        }
    )

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
                        "value": "FRP",
                        "values": ["FRP", "ARP", "FBR"],
                        "label": "Ordering Policy",
                    },

    "mu": Slider("Demand μ [unit]", 10, 1, 50, 1),
    "sigma": Slider("Demand σ [unit]", 5, 1, 20, 1),
    "alpha": Slider("Congestion sensitivity (α) [ad]", 0.33, 0.0, 1.0, 0.01),
    "beta": Slider("Empty truck speed factor (β) [ad]", 1.03, 1.0, 2.0, 0.01),
    "L_0": Slider("Free-flow lead time [days]", 3, 1, 5, 0.33),
    "k": Slider("Safety factor (k) [ad]", 2.33, 1.0, 3.0, 0.01),
    "truck_movement": Slider("Truck movement per step [ad]", 1.5, 0.1, 5.0, 0.1),
    "p": Slider("Unit stockout penalty [€/unit]", 1.0, 0.0, 10.0, 0.1),
    "h": Slider("Unit holding cost [€/unit]", 0.01, 0.0, 1.0, 0.01),
    "c": Slider("Unit transport cost [€/unit]", 0.01, 0.0, 1.0, 0.01),
    "n_trucks": Slider('Number of trucks [ad]', 8, 1, 20, 1),
}


# ======================
# Cost plot
# ======================
#editing the plot style
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
    post_process = post_process_lines #function for customizing the plot
)


# ======================
# Model & visualization
# ======================
page = SolaraViz(
                SupplyChainModel(),
                components=[
                    CostPlot,
                    get_costs,
                    model_info,
                ],
                model_params=model_params,
                name="Supply Chain Model",
            )

page