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

# =================================
# Cost report summary & KPIS & Info
# =================================
#cost report
def get_costs(model: SupplyChainModel):
    text = (
        f"### Supply Chain Costs\n"
        f"- **Step [unit]:** {model.steps}\n"
        f"- **Times stockout [ad]:** {model.times_stockout}\n"
        f"- **Stockout cost:** {model.stockout_cost:.2f} €\n"
        f"- **Holding cost:** {model.hold:.2f} €\n"        
        f"- **Transportation cost:** {model.transportation:.2f} €\n"
        f"- **Total cost:** {model.hold + model.stockout_cost + model.transportation:.2f} €\n"
    )
    return solara.Markdown(
        text,
        style={
        }
    )
#kpis
def get_kpi(model: SupplyChainModel):
    kpis = model.compute_kpis()
    text = (
        f"### KPIs\n\n"
        f"- **AVG lead time [unit]:** {kpis['avg_lead_time']:.2f}\n"
        f"- **CV lead time [ad]:** {kpis['cv_lead_time']:.2f}\n"
        f"- **AVG traffic [ad]:** {kpis['avg_traffic']:.2f} %\n"
        f"- **CV warehouse [ad]:** {kpis['cv_inventory']:.2f}\n"
    )
    return solara.Markdown(
        text,
        style={
        }
    )
#info
def model_info(model: SupplyChainModel):
    text_info = (
        f"**Info**  \n"
        f"The model is composed of a total of {len(model.agents)} agents: one *factory agent*, responsible for producing inventory, "
        f"one *customer agent*, responsible for purchasing and holding stock, and the rest are *truck agents* that enable the "
        f"transportation of goods between the factory and the customer.  \n"
        f"The panel on the left allows to tweak the model hyperparameters in order to explore different scenarios. "
        f"The most relevant is the *Ordering policy*, which determines the inventory replenishment strategy adopted by the customer.  \n"
        f"The plot on the left shows the evolution of different cost components over time, the one on the right shows the evolution of the lead time.\n"
        f"The 'Costs' panel enlists the various costs, while the 'KPIs' panel enlists the main KPIs.  \n"
        f"*Times stockout:* number of occurerences the customer ran out of stock during the simulation.\n"
        f"*Stockout cost:* cumulative cost incurred due to stockouts.\n"
        f"*Holding cost:* cumulative cost of holding inventory.\n"
        f"*Transportation cost:* cumulative cost of transporting goods.  \n"
        f"AVG stands for average, CV stands for coefficient of variation (std/mean). [ad] stands for adimensional quantity."
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
    "sigma": Slider("Demand σ [unit]", 5, 0.1, 15, 0.25),
    "alpha": Slider("Congestion sensitivity (α) [ad]", 0.75, 0.0, 2.0, 0.01),
    "beta": Slider("Empty truck speed factor (β) [ad]", 1.1, 1.0, 1.5, 0.005),
    "L_0": Slider("Free-flow lead time (L0) [unit]", 3, 0.1, 10, 0.25),
    "k": Slider("Safety factor (k) [ad]", 2.33, 1.0, 3.0, 0.01),
    "truck_movement": Slider("Truck movement per step [ad]", 1, 0.1, 5.0, 0.1),
    "p": Slider("Unit stockout penalty [€/unit]", 25.0, 0.0, 100.0, 1),
    "h": Slider("Unit holding cost [€/unit]", 1.5, 0.0, 50.0, 0.5),
    "c": Slider("Unit transport cost [€/unit]", 4, 0.0, 50.0, 0.5),
    "n_trucks": Slider('Number of trucks [ad]', 8, 1, 20, 1),
}


# ===========================
# Cost plot & Lead time plot
# ===========================
#editing the plot style
def post_process_lines_cost_plot(ax):
    # figure dimension
    ax.figure.set_size_inches(6, 4) 
    # axis titles
    ax.set_xlabel("Steps [unit]", fontsize=10)
    ax.set_ylabel("Cost [€]", fontsize=10)
    # Ticks axes
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    #change lines thickness
    for line in ax.lines:
        line.set_linewidth(2)

CostPlot = make_plot_component(
    {
        "stockout": "red",
        "holding": "blue",        
        "transportation": "orange",
    },
    backend="matplotlib", #graphic library used in backend
    post_process = post_process_lines_cost_plot #function for customizing the plot
)

#the same as above, but for the lead time plot
def post_process_lt(ax):
    ax.figure.set_size_inches(6, 4)
    ax.set_xlabel("Steps [unit]", fontsize=10)
    ax.set_ylabel("Lead time [unit]", fontsize=10)
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    for line in ax.lines:
        line.set_linewidth(2)

LeadTimePlot = make_plot_component(
    {
        "lead_time": "green"
    },
    backend="matplotlib",
    post_process=post_process_lt,
)

# ======================
# Model & visualization
# ======================
page = SolaraViz(
                SupplyChainModel(),
                components=[
                    CostPlot,
                    LeadTimePlot,
                    get_costs,
                    get_kpi,
                    model_info,
                ],
                model_params=model_params,
                name="Supply Chain Model",
            )

page