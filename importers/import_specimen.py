from models import Specimen, DonorType, CellSpecimen, HumanDonor

def import_specimen(session, donor_id, row):
    specimen_type = session.query(Specimen).filter_by(type="cell").first()
    if not specimen_type:
        specimen_type = Specimen(name="cell")
        session.add(specimen_type)

    donor_type = session.query(DonorType).filter_by(name="human").first()
    if not donor_type:
        donor_type = DonorType(name="human")
        session.add(donor_type)

    cell_type = session.query(CellSpecimen).filter_by(name="PBMC").first()
    if not cell_type:
        cell_type = CellSpecimen(name="PBMC", specimen_type=specimen_type, donor_type=donor_type)
        session.add(cell_type)

    human_donor = session.query(HumanDonor).filter_by(name=str(donor_id)).first()
    if not human_donor:
        human_donor = HumanDonor(
            name=str(donor_id),
            age=row.get("age"),
            sex=row.get("sex"),
            weight_kg=row.get("weight_kg"),
            height_cm=row.get("height_cm"),
            bmi=row.get("bmi"),
            class_bmi=row.get("Class_BMI"),
            class_weight=row.get("Class_weight"),
            ethnicity=row.get("ethicity"),
            donor_class=row.get("Class"),
            cell_type=cell_type,
        )
        session.add(human_donor)
        session.flush()
    return human_donor