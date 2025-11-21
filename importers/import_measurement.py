from models import Measurement

def get_or_create_default_measurement(session, well):
    measurement = session.query(Measurement).filter_by(
        name="default_measurement",
        well_id=well.id).first()
    if not measurement:
        measurement = Measurement(
            name="default_measurement",
            instrument_name="default_instrument",
            settings={"default": True},
            well_id=well.id
        )
        session.add(measurement)
        session.flush()
    return measurement