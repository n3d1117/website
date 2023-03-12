---
title: Design and development of components for the AirQino platform dedicated to air quality monitoring
description: A recap of my master's thesis in Computer Science & Engineering about the AirQino platform and related developments.
date: 2022-04-11T09:24:54.000Z
slug: masters-thesis-airqino
tags: [uni, thesis, airqino]
toc: true
math: false
comments: true
---

{{< note variant="info" >}}
This post is a recap of my master's thesis in Computer Science & Engineering, which I wrote in collaboration with [Magenta srl](https://magenta.it/) and the [Institute of BioEconomy (IBE) of CNR](https://www.ibe.cnr.it).
{{< /note >}}

## Abstract
Air pollution is currently one of the main issues affecting urbanized areas worldwide. There is concern regarding the health issues caused by long-term exposure to airborne particulate matter (PM) and other harmful gases (such as NO2, CO2 and O3).
Measurements at appropriate spatial and temporal scales are essential for understanding and monitoring air pollution, which is required for the development of real-time strategies for exposure control.

Conventional approaches to air quality monitoring are based on networks of static and sparse measurement stations, provided by regional or national environmental protection agencies. These stations, however, have limitations due to coarse spatial coverage of the whole municipality, low time-frequency, and high costs.

New low-cost and high-portability sensors, intended to complement the existing solutions, are radically changing the conventional approach by allowing real-time information in a high-density form, with new scalable networks (such as [AirQino](https://airqino.it/en/)) providing data at fine spatial and temporal scales.

This thesis, developed in collaboration with [Magenta srl](https://magenta.it/) and the [Institute of BioEconomy (IBE) of CNR](https://www.ibe.cnr.it), focuses on the AirQino platform and has three main objectives: (i) to improve efficiency and scalability of the system; (ii) to investigate and compare different techniques aimed at improving accuracy of the sensors’ calibration process; (iii) to develop a web interface to make batch calibration easier.

## AirQino
[AirQino](https://airqino.it/en/) is a low-cost air quality monitoring system that can be used to measure various pollutants in the air. The platform consists of a small device that can be easily installed and connected to a Wi-Fi network. 

It uses sensors to measure levels of particulate matter, carbon monoxide, nitrogen dioxide, and other harmful gases. The data collected by the device is sent to a web portal where it can be accessed and analyzed by users. The web portal provides real-time data on air quality and allows users to view historical data as well. The platform is designed for use in both indoor and outdoor environments and can be used by individuals, organizations, and communities to monitor air quality in their local area.

Overall, the AirQino platform provides an affordable and accessible solution for monitoring air quality that can help improve public health and environmental protection efforts.

### Architecture
The platform is composed of a hardware device and a software system that work together to collect, process, and analyze air quality data. 

- The hardware device includes sensors for measuring various pollutants in the air, such as particulate matter, carbon monoxide, nitrogen dioxide, and ozone.
- The software system includes a web portal that allows users to access real-time and historical data on air quality. The portal provides various features such as data visualization tools and user management capabilities. 

### Sensors
- The [MiCS-2714](https://www.sgxsensortech.com/content/uploads/2014/08/1107_Datasheet-MiCS-2714.pdf) sensor is used to detect nitrogen dioxide (NO2) in the air. It is a metal oxide semiconductor (MOS) sensor that consists of a film deposited on a plate of heating elements whose operating temperature is generally between 300°C and 500°C. The most suitable functional material for detecting NO2 is lanthanum iron oxide (LaFeO3), which has good sensitivity to nitrogen oxides and low sensitivity to carbon monoxide. The section includes a photo of the sensor and its circuit diagram.

- The [SDS011](https://cdn-reichelt.de/documents/datenblatt/X200/SDS011-DATASHEET.pdf) sensor is used to detect particulate matter with a diameter of 2.5 micrometers or less (PM2.5) and PM10. It is an optical particle counter that uses laser scattering to detect particles in the air. The section includes a photo of the sensor and its circuit diagram.

## Development
- [Replication of the production database](/blog/2021/10/streaming-replication-docker-timescale/): this development involves replicating the production database to a secondary server, which can be used for backup and disaster recovery purposes. This ensures that data collected by the AirQino platform is not lost in case of a system failure or other unforeseen events.

- [Optimization of database queries](/blog/2021/11/continuous-aggregates-timescale/): this development involves optimizing the database queries used by the AirQino platform to improve query response times for particularly demanding queries. This ensures that users can access real-time data on air quality without experiencing delays or other performance issues.

## Calibration
 Calibration is an essential step in ensuring that the sensors used in the platform provide accurate and reliable data on air quality. This section provides an overview of the calibration process and its importance in ensuring accurate measurements.

1. **Introduction to the calibration process**: This section provides an overview of the calibration process and its importance in ensuring accurate measurements of air quality.

2. **Available datasets and preprocessing**: This section describes the datasets used for calibration and how they were preprocessed to ensure their suitability for use in the AirQino platform.

3. **Theoretical overview of regression concepts**: this section provides a brief theoretical overview of regression concepts such as correlation, metrics (correlation coefficient, determination coefficient, mean square error), residual analysis, and regression models (both linear and nonlinear).

The section called "Discussione" provides a discussion of the results obtained from the calibration process and their implications for the AirQino platform. The section highlights several key points, including:

1. **Comparison of different regression models**: This section compares the performance of different regression models (linear and nonlinear) in predicting air quality measurements. The results show that nonlinear models generally perform better than linear models, particularly for predicting PM2.5 concentrations.

2. **Importance of preprocessing techniques**: This section emphasizes the importance of preprocessing techniques such as data cleaning and feature selection in improving the accuracy of air quality predictions.

3. **Limitations and future work**: This section discusses some limitations of the calibration process, such as the limited availability of high-quality datasets for calibration purposes. It also suggests some areas for future work, such as exploring new regression models or incorporating additional sensors into the AirQino platform.

Overall, the section emphasizes that while there are some limitations to the calibration process, it has provided valuable insights into how to improve the accuracy and reliability of air quality measurements using the AirQino platform. By continuing to refine calibration techniques and explore new approaches to air quality monitoring, this platform can help individuals and communities make informed decisions about their exposure to harmful pollutants in their local environment.

## Web interface
Development and implementation of a web-based interface for the AirQino calibration platform. The interface is designed to simplify the process of calibrating multiple AirQino devices simultaneously, making it easier for individuals and organizations to monitor air quality in their local area.

## References
- [GitHub repo](https://github.com/n3d1117/airqino-calibration)
- [Thesis PDF](https://github.com/n3d1117/airqino-calibration/blob/master/thesis/thesis/thesis.pdf) (in italian)
- [Presentation PDF](https://github.com/n3d1117/airqino-calibration/blob/master/thesis/presentation/presentation.pdf) (in italian)