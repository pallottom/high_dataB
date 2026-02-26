from models import Measurement

def get_or_create_default_measurement(session, well):
    measurement = session.query(Measurement).filter_by(
        type="measurement",
        well_id=well.id).first()
    if not measurement:
        measurement = Measurement(
            type="measurement",
            well_id=well.id
        )
        session.add(measurement)
        session.flush()
    return measurement