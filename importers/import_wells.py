from models import Well

def import_well(session, plate, human_donor, well_key, row, col):
    well = session.query(Well).filter_by(well_key=well_key, col=col, row=row, plate=plate).first()
    if not well:
        well = Well(well_key=well_key, col=col, row=row, plate=plate, donor=human_donor)
        session.add(well)
    elif well.donor is None:
        well.donor = human_donor
    return well