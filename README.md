# USV ROS2 COPPELIASIM INTEGRATED SIMULATION
This repo is refered to a personal project of Unmaned Surface Vehicle (USV), the modeling was maden with ROS2 and its integrated with CoppeliaSim by API to virtual, real time developed control algorithms validation.

# INTRODUCTION
Over the autonomous navigation field trajectory control is often discussion on the state of art, the principal implications of more effective tracjectory control methods are faster movementation and fuel consumption eficiency. With this in mind, this simulation works as a study of virtual validation of such algorithms.

# METODOLOGY
The ROS2 code of the system receives real time motion data, linear and angular positions, velocities and aceleration, this data is collected by API, and sent to the controler by ROS2 comunication tools, topics and services are used to send the motion data and reference trajectory to the controler node by interfaces, also, the control signals are sent to Coppelia to apply the correpondent forces. This intends do simulate the more realistically possible the real behavior of a shipment. Below, the grahp with nodes and interfaces comunications:

<img width="1191" height="495" alt="image" src="https://github.com/user-attachments/assets/dc2e4aa5-69ab-4466-b912-1a8456d56339" />
<h1 align="center">Figure 01: ROS2 CoppeliaSim USV Simulation Graph.</h1>
