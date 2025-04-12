from datetime import datetime, timedelta

# --- Log Overspending ---
def log_overspending(conn, transaction_id, expected_cost, actual_cost, employee_id, current_date, type='delivery'):
    deviation = actual_cost - expected_cost
    # Log only if the actual cost exceeds expected by more than 10%
    if deviation > expected_cost * 0.1:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO overspending_log (
                        transaction_id, type, expected_cost, actual_cost, deviation,
                        reason, flagged_by, date_time, employee_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, 'system', %s, %s);
                """, (
                    transaction_id,
                    type,
                    expected_cost,
                    actual_cost,
                    deviation,
                    f"{type.title()} cost exceeded expected threshold",
                    current_date,
                    employee_id
                ))
            conn.commit()
        except Exception as e:
            print(f"Error logging overspending: {e}")

# --- Log Underperformance ---
def log_underperformance(conn, delivery_id, entity_type, entity_id, event_type, expected_duration, actual_duration, current_date, reason=None):
    """
    Inserts a record into underperformance_log if the delay exceeds 30 minutes.
    The new column delivery_id is logged as well.
    """
    deviation = actual_duration - expected_duration
    if deviation.total_seconds() > 1800:  # Only log if delay exceeds 30 minutes
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO underperformance_log (
                        delivery_id, entity_type, entity_id, event_type,
                        expected_duration, actual_duration, deviation,
                        reason, flagged_by, date_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'system', %s);
                """, (
                    delivery_id,
                    entity_type,
                    entity_id,
                    event_type,
                    expected_duration,
                    actual_duration,
                    deviation,
                    reason or f"{event_type} exceeded expected time",
                    current_date
                ))
            conn.commit()
        except Exception as e:
            print(f"Error logging underperformance: {e}")

# --- Log Delivery Anomalies ---
def log_delivery_anomalies(conn, transaction_id, expected_cost, actual_cost, driver_id, delivery_start, delivery_end, current_date, delivery_id):
    """
    Logs delivery anomalies by recording overspending events and underperformance
    (i.e. delivery delays beyond 30 minutes). The new delivery_id is passed to the
    underperformance log.
    """
    # Log overspending (cost deviations)
    log_overspending(conn, transaction_id, expected_cost, actual_cost, driver_id, current_date, type='delivery')
    
    # Calculate delivery duration and log underperformance if needed.
    expected_duration = timedelta(hours=3)
    actual_duration = delivery_end - delivery_start
    log_underperformance(
        conn,
        delivery_id,
        entity_type='truck',
        entity_id=driver_id,
        event_type='delivery_delay',
        expected_duration=expected_duration,
        actual_duration=actual_duration,
        current_date=current_date,
        reason="Delivery took longer than expected"
    )
