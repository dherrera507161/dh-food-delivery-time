-- For queries designed in order to answer the questions

-- Question 1: Top 5 customer areas with highest average delivery time in the last 30 days
SELECT customer_area, ROUND(AVG(delivery_time_min),2) AS avg_time
FROM deliveries.csv -- Include .csv if running locally, delete .csv if running with a dedicated SQL server
WHERE order_placed_at >= CURRENT_DATE - INTERVAL '30 days' -- Could change NOW() vs CURRENT_DATE depending on precision wanted
GROUP BY customer_area
ORDER BY avg_time DESC
LIMIT 5;

-- Question 2: Average delivery time per traffic contitions, by restaurant area and cuisine type

SELECT 
c.area,
c.cuisine_type,
b.traffic_condition,
ROUND(AVG(b.delivery_time_min),2) AS avg_time
FROM orders.csv AS a
INNER JOIN deliveries.csv AS b
ON a.delivery_id=b.delivery_id
INNER JOIN restaurants.csv AS c
ON a.restaurant_id=c.restaurant_id
GROUP BY b.traffic_condition,c.area,c.cuisine_type
ORDER BY c.area ASC,c.cuisine_type ASC,b.traffic_condition ASC
;

-- Question 3: Top 10 delivery people with the fastest average delivery time, 
--considering only those with at least 50 deliveries and who are still active

SELECT
a.delivery_person_id, 
a.name AS name_dvr,
ROUND(AVG(b.delivery_time_min),2) AS avg_time,
FROM delivery_persons.csv AS a
LEFT JOIN deliveries.csv AS b
ON a.delivery_person_id=b.delivery_person_id
WHERE a.is_active=True
GROUP BY a.delivery_person_id,a.name
HAVING COUNT(b.delivery_id)>=50 -- Tested with 10 as artificial data has no person with over 50 deliveries
ORDER BY avg_time ASC
LIMIT 10
;

-- Question 4: The most profitable restaurant areas in the last 3 months, defined as the area with the highest total order value.
SELECT a.restaurant_area, SUM(b.order_value) AS total
FROM deliveries.csv AS a
INNER JOIN orders.csv AS b
ON a.delivery_id=b.delivery_id
WHERE a.order_placed_at >= CURRENT_DATE - INTERVAL '3 months' 
GROUP BY a.restaurant_area
ORDER BY total DESC
LIMIT 1
;
-- Question 5: Identify whether any delivery people show an increasing trend in average delivery time 

--MONTHLY=TABLE THAT SHOWS THE AVERAGE PER MONTH
WITH monthly AS(
SELECT
a.delivery_person_id, 
b.name,
EXTRACT (YEAR FROM a.order_placed_at)*100 + EXTRACT (MONTH FROM a.order_placed_at) AS year_month,
ROUND (AVG(a.delivery_time_min),2) AS avg_time
FROM deliveries.csv AS a
INNER JOIN delivery_persons.csv AS b
ON a.delivery_person_id=b.delivery_person_id -- I would add a filter here to reduce computation time for the last 2 months, depending if this query is either for a dashboard or just as a punctual query
GROUP BY (a.delivery_person_id,b.name,year_month)
ORDER BY a.delivery_person_id ASC, year_month DESC
), 
--WINDOWS=TABL# THAT CALCULATES THE DIFFERENCE BETWEEN THE LAST MONTH AND THE MONTH BEFORE, AND CALCULATES THE PERCENTAGE CHANGE
windows AS (
SELECT 
delivery_person_id,
name,
year_month,
avg_time,
LEAD(avg_time,1) OVER (PARTITION BY delivery_person_id ORDER BY year_month DESC) AS last_month_avg_time,
ROUND((100*(avg_time - LEAD(avg_time,1) OVER (PARTITION BY delivery_person_id ORDER BY year_month DESC))/LEAD(avg_time,1) OVER (PARTITION BY delivery_person_id ORDER BY year_month DESC)),2) AS diff_avg_time,
ROW_NUMBER() OVER (PARTITION BY delivery_person_id ORDER BY year_month DESC) AS rank
FROM monthly
ORDER BY delivery_person_id ASC, year_month DESC
)
--FINAL TABLE= SHOWS THE TREND AND FILTERS OUT THE LAST DELIVERY MONTH OF EACH DRIVER
SELECT *,
CASE
    WHEN diff_avg_time IS NULL THEN 'Insufficient history'
    WHEN diff_avg_time > 0 THEN 'Increasing'
    WHEN diff_avg_time < 0 THEN 'Decreasing'
    ELSE 'Same'
END AS delivery_trend
FROM windows
WHERE rank=1 -- This can be changed to CURRENT_DATE depending on the desired problem (Either compare the last month of each driver, or just the current month and filter out drivers that have not delivered in the current month)
;