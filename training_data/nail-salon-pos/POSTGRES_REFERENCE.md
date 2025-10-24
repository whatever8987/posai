# PostgreSQL vs MySQL Syntax Reference

Quick reference for the differences you'll encounter.

## 🔄 Date Functions

| Operation | MySQL ❌ | PostgreSQL ✅ |
|-----------|---------|--------------|
| Current date | `CURDATE()` | `CURRENT_DATE` |
| Current time | `NOW()` | `CURRENT_TIMESTAMP` |
| 7 days ago | `DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)` | `CURRENT_DATE - INTERVAL '7 days'` |
| Add days | `DATE_ADD(date, INTERVAL 7 DAY)` | `date + INTERVAL '7 days'` |
| Extract month | `MONTH(date)` | `EXTRACT(MONTH FROM date)` |
| Extract year | `YEAR(date)` | `EXTRACT(YEAR FROM date)` |
| Week start | `WEEK(date)` | `date_trunc('week', date)` |
| Format date | `DATE_FORMAT(date, '%Y-%m-%d')` | `TO_CHAR(date, 'YYYY-MM-DD')` |

## 📝 String Functions

| Operation | MySQL ❌ | PostgreSQL ✅ |
|-----------|---------|--------------|
| Concatenate | `CONCAT(a, b)` | `a \|\| b` |
| Case insensitive | `LIKE` | `ILIKE` |
| Find position | `LOCATE('x', str)` | `POSITION('x' IN str)` |
| Substring | `SUBSTRING(str, 1, 10)` | `SUBSTRING(str FROM 1 FOR 10)` |

## 🔢 Aggregate Functions

| Operation | MySQL ❌ | PostgreSQL ✅ |
|-----------|---------|--------------|
| Median | `MEDIAN(col)` | `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY col)` |
| Group concat | `GROUP_CONCAT(col)` | `STRING_AGG(col, ',')` |

## 📊 Common Query Examples

### This Month's Revenue
```sql
-- MySQL ❌
SELECT SUM(total_amount) 
FROM bookings 
WHERE MONTH(booking_date) = MONTH(CURRENT_DATE)
  AND YEAR(booking_date) = YEAR(CURRENT_DATE)
  AND status = 'completed';

-- PostgreSQL ✅
SELECT SUM(total_amount) as monthly_revenue
FROM bookings 
WHERE EXTRACT(MONTH FROM booking_date) = EXTRACT(MONTH FROM CURRENT_DATE)
  AND EXTRACT(YEAR FROM booking_date) = EXTRACT(YEAR FROM CURRENT_DATE)
  AND status = 'completed';
```

### Last 7 Days
```sql
-- MySQL ❌
SELECT SUM(total_amount)
FROM bookings
WHERE booking_date >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
  AND status = 'completed';

-- PostgreSQL ✅
SELECT SUM(total_amount) as weekly_revenue
FROM bookings
WHERE booking_date >= CURRENT_DATE - INTERVAL '7 days'
  AND status = 'completed';
```

### Customer Names
```sql
-- MySQL ❌
SELECT CONCAT(first_name, ' ', last_name) as full_name
FROM customers;

-- PostgreSQL ✅
SELECT first_name || ' ' || last_name as full_name
FROM customers;
```

### This Week's Appointments
```sql
-- MySQL ❌
SELECT COUNT(*)
FROM bookings
WHERE WEEK(booking_date) = WEEK(CURRENT_DATE)
  AND YEAR(booking_date) = YEAR(CURRENT_DATE);

-- PostgreSQL ✅
SELECT COUNT(*)
FROM bookings
WHERE booking_date >= date_trunc('week', CURRENT_DATE)
  AND booking_date < date_trunc('week', CURRENT_DATE) + INTERVAL '1 week';
```

## 🔧 Fix Your Training

If you're getting MySQL syntax errors, run:

```bash
python train_postgres_syntax.py
```

This will retrain your model with PostgreSQL syntax!

## 💡 Tips

1. **Always specify intervals with quotes**: `INTERVAL '7 days'` not `INTERVAL 7 DAY`
2. **Use ILIKE for case-insensitive search**: `name ILIKE '%john%'`
3. **Use || for concatenation**: `first_name || ' ' || last_name`
4. **Use EXTRACT for date parts**: `EXTRACT(MONTH FROM date)`
5. **Use date_trunc for week/month start**: `date_trunc('week', date)`

## 🚀 After Retraining

Your questions will work properly:
- "What is our revenue this week?" ✅
- "Show customers from last month" ✅
- "Who hasn't visited in 60 days?" ✅

All using correct PostgreSQL syntax!

