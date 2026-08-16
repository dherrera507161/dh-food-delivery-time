#SQL INSIGHTS

In order to understand more of the business problem, I would perfomr the following queries. 
I also want to note, if handling raw,real data (not artificial like the created ones) I would do additional queries to verify there are no data duplicates or irrational values (i.e delivery time below zero)
Nevertheless, I am limiting my answer to the ones most applicable from a business Point of View:

## 1. I want to find out the top 20 customers with the highest total order value, with their respective total deliveries and average order value. I would this in order to find out who are my most valuable customers that I need to ensure I maintain through promotions and discounts. Furthermore, I could also group this information by region/cuisine_type so I collaborate my strongly with the restaurants present in the area that is bringing me more value.

SELECT
    o.customer_id,
    COUNT(*) AS n_deliveries,
    ROUND(SUM(o.order_value), 2) AS total_order_value,
    ROUND(AVG(o.order_value), 2) AS avg_order_value
FROM orders.csv  AS o
GROUP BY o.customer_id
ORDER BY total_order_value DESC
LIMIT 20;

##  2. I want to do a monthly summary of the avg rating, avg distance, avg distance and avg speed (distance/time). This is because I want to find out: 1. How much the delivery time is affected by the month/season (i.e delivery speed being lower in the winter vs. spring or consumers feeling more comfortable ordering from longer distances) 2. What is the relation between delivery time and rating and can I expect my customer satisfaction rating/app usage to be lower in colder vs. hotter months? . 

SELECT
    EXTRACT(YEAR FROM d.order_placed_at)*100 + EXTRACT(MONTH FROM d.order_placed_at) AS year_month,
    COUNT(*) AS n_deliveries,
    ROUND(AVG(d.delivery_rating), 2) AS avg_rating,
    ROUND(AVG(d.delivery_time_min), 2) AS avg_delivery_time_min,
    ROUND(AVG(d.delivery_distance_km), 2) AS avg_distance_km,
    ROUND(AVG(d.delivery_distance_km / NULLIF(d.delivery_time_min, 0)), 3) AS avg_speed_km_per_min
FROM deliveries.csv AS d
GROUP BY year_month
ORDER BY year_month;

##  3. I want to do a driver dashboard (only using active drivers) that recounts their months of experience, total_deliveries ,avg rating and avg actual delivery time (Actual Delivery Time = Delivery Time - Average Preparation Time). This is to have an estimation of how much experienced vs. new drivers affect the quality of the service in terms of delivery time and customer satisfaction.

SELECT
    dp.delivery_person_id, dp.name, dp.is_active,
    DATE_DIFF('month', dp.hired_date, CURRENT_DATE) AS months_experience,
    COUNT(*) AS n_deliveries,
    ROUND(AVG(d.delivery_rating), 2) AS avg_rating,
    ROUND(AVG(d.delivery_time_min), 2) AS avg_delivery_time_min,
    ROUND(AVG(d.delivery_time_min - r.avg_preparation_time_min), 2) AS avg_actual_delivery_time_min,
    ROUND(AVG(d.delivery_distance_km), 2) AS avg_distance_km,
    ROUND(AVG(d.delivery_distance_km / NULLIF(d.delivery_time_min, 0)), 3) AS avg_speed_km_per_min
FROM deliveries.csv AS d
JOIN delivery_persons.csv AS dp ON dp.delivery_person_id = d.delivery_person_id
JOIN orders.csv AS o ON o.delivery_id = d.delivery_id
JOIN restaurants.csv AS r ON r.restaurant_id = o.restaurant_id
GROUP BY dp.delivery_person_id, dp.name, dp.is_active, dp.hired_date
ORDER BY avg_speed_km_per_min DESC;

## 4. I want to do a comparison of weekday vs weekend days for  every customer area with key information: Avg_Order_Value, avg_rating, avg_delivery_time and average actual delivery time (See Q3). This is to know how does the area where the order depends on a day-to-day basis. For example, to verify the assumption that I need to focus more drivers on the residential areas during the weekends and to focus more areas in the work districts during the workdays.

WITH base AS (
    SELECT
        d.*,
        o.order_value,
        r.avg_preparation_time_min,
        CASE WHEN EXTRACT(DOW FROM d.order_placed_at) IN (0,6) THEN 'Weekend' ELSE 'Weekday' END AS day_type
    FROM deliveries.csv AS d
    JOIN orders.csv AS o ON o.delivery_id = d.delivery_id
    JOIN restaurants.csv AS r ON r.restaurant_id = o.restaurant_id
)
SELECT
    customer_area,
    day_type,
    COUNT(*) AS n_deliveries,
    ROUND(AVG(order_value), 2) AS avg_order_value,
    ROUND(AVG(delivery_rating), 2) AS avg_rating,
    ROUND(AVG(delivery_time_min), 2) AS avg_delivery_time_min,
    ROUND(AVG(delivery_time_min - avg_preparation_time_min), 2) AS avg_actual_delivery_time_min,
    ROUND(AVG(delivery_distance_km), 2) AS avg_distance_km,
    ROUND(AVG(delivery_distance_km / NULLIF(delivery_time_min, 0)), 3) AS avg_speed_km_per_min
FROM base
GROUP BY customer_area, day_type
ORDER BY customer_area, day_type;
 
## 5. Summary table of traffic,weather_condition, rating, delivery time, and actual delivery time. Similar to Query #2 of the original statement, I would like to focus more on issues like weather,traffic and how this affects the delivery time of my drivers. 

SELECT
    d.traffic_condition, d.weather_condition, COUNT(*) AS n_deliveries,
    ROUND(AVG(d.delivery_rating), 2) AS avg_rating,
    ROUND(AVG(d.delivery_time_min), 2) AS avg_delivery_time_min,
    ROUND(AVG(d.delivery_time_min - r.avg_preparation_time_min), 2) AS avg_actual_delivery_time_min,
    ROUND(AVG(o.order_value), 2) AS avg_order_value,
    ROUND(AVG(d.delivery_distance_km), 2) AS avg_distance_km,
    ROUND(AVG(d.delivery_distance_km / NULLIF(d.delivery_time_min, 0)), 3) AS avg_speed_km_per_min
FROM deliveries.csv AS d
JOIN orders.csv AS o ON o.delivery_id = d.delivery_id
JOIN restaurants.csv AS r ON r.restaurant_id = o.restaurant_id
GROUP BY d.traffic_condition, d.weather_condition
ORDER BY d.traffic_condition, d.weather_condition;