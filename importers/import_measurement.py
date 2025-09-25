from models import Measurement

def get_or_create_default_measurement(session):
    measurement = session.query(Measurement).filter_by(name="default_measurement").first()
    if not measurement:
        measurement = Measurement(
            name="default_measurement",
            instrument_name="default_instrument",
            settings={"default": True}
        )
        session.add(measurement)
        session.flush()
    return measurement