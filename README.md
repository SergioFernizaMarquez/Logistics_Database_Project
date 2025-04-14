# Logistics_Database_Project

My project is an end-to-end simulation and analysis of a logistics operation. The project covers every stage of the process: from building the database and defining operational behaviors, to generating and inserting data, running a multi-year simulation, and finally performing exploratory data analysis, predictive modeling, and cost analytics.

## Overview

I built a comprehensive database system that supports logistics operations including inventory management, order processing, truck and employee management, supplier deliveries, and financial transaction logging. Using Python scripts, I simulated operations over multiple years, generated synthetic data, and populated the database. I then used Jupyter Notebook for exploratory data analysis, visualization, demand forecasting, and cost efficiency comparisons. This project ultimately aims to improve our logistics performance and demonstrate potential cost savings.

## Database Design and Schema

The database schema consists of several core tables:

* **Store**  
  Contains details such as name, address, distance from the warehouse, expected travel time, and operating hours.

* **Pending Orders**  
  Records customer orders awaiting processing.

* **Product Pellets Summary and Product Pellet**  
  Track aggregated product information and individual pellet details including cost, weight, and expiration.

* **Inventory**  
  Provides an overview of current stock, items scheduled for delivery, and incoming supplier orders.

* **Employee**  
  Maintains records of drivers and staff.

* **Truck**  
  Records details for delivery trucks, including capacity, fuel metrics, kilometers driven, operational status, and maintenance dates.

* **Inventory Delivery, Truck Log, Transactions, Fuel Log, Payroll Log**  
  Log outbound deliveries, truck routes, financial transactions, fuel purchases, and payroll information.

* **Supplier and Supplier Delivery**  
  Track supplier relationships and incoming delivery details.

* **Overspending Log and Underperformance Log**  
  Log anomalies related to expenses and performance for further analysis.

## Operational Behaviors and Simulation

I implemented various Python modules to simulate logistics operations:

* **Order Behavior**  
  Processes customer orders, schedules truck deliveries, updates inventory, and logs transactions.

* **Restock Behavior**  
  Processes supplier deliveries, inserts new pellet records, and updates inventory counts accordingly.

* **Payroll and Fuel Behaviors**  
  Handle employee payroll and truck fuel refilling.

These behaviors are integrated into a daily simulation that

* Removes expired products  
* Updates truck maintenance statuses  
* Restocks inventory based on demand thresholds  
* Processes payroll and fuel transactions  
* Processes new customer orders  
* Fulfills orders and logs performance metrics

## Data Generation and Insertion

I developed scripts to generate realistic synthetic data for inventory levels, orders, deliveries, fuel consumption, and financial transactions. The generated data populates the database and forms the basis for simulation and analysis.

## Multi-Year Simulation

The simulation runs over multiple years to mimic real-world operations. This longitudinal data is used for trend analysis, time series forecasting, and performance evaluation.

## Exploratory Data Analysis and Visualization

In the Jupyter Notebook, I performed exploratory data analysis with visualizations that include

* Time series and trend analysis of orders and inventory  
* Performance metrics for drivers and trucks  
* Financial analysis of transactions across different types  
* Outlier detection and anomaly analysis

## Predictive Modeling and Cost Analytics

I built forecasting models, such as ARIMA, for monthly demand for each product. These forecasts inform the determination of optimal monthly restock quantities and cost comparisons. I then computed and compared the historical restock cost with the new forecasted cost and derived the price margin necessary to achieve a 1% profit margin.

### Interactive Tableau Dashboard

I created an interactive Tableau dashboard that presents a comprehensive view of our logistics operations. The dashboard features detailed visualizations of key metrics such as monthly transaction costs, net revenue trends, fuel expenses, and driver performance. By exploring the dashboard, you can dive into operational insights and identify optimization opportunities in our supply chain. You can access the live dashboard [here](https://public.tableau.com/views/Logistics_17445446866560/Dashboard2?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link) and interact with the data in real time.

## How to Run the Project

1. **Database Setup**  
   Initialize the PostgreSQL database using the provided schema.

2. **Data Population**  
   Run the data generation and insertion scripts to populate the database with synthetic data.

3. **Operational Simulation**  
   Execute the simulation scripts to generate multi-year operational data.

4. **Analysis Notebook**  
   Open the Jupyter Notebook to perform EDA, forecast demand, and conduct financial cost analyses.

5. **Predictive Modeling**  
   Run the forecasting and optimization code to evaluate potential improvements in restocking efficiency and profitability.

6. **Tableau Dashboard**
   In tableau build WorkSheets for the data obtained, so far. Then use them to implement a Dashboard.

## Conclusion

This project demonstrates a complete end-to-end solution for managing logistics operations, from database creation and simulation to analysis and forecasting. The insights gained from EDA and predictive modeling will guide future enhancements in cost savings, inventory management, and overall operational efficiency.

