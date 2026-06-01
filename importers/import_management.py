from models import Project, Screen, Plate, Location


def _get_management_cache(session):
    cache = session.info.get("management_cache")
    if cache is not None:
        return cache

    projects_by_group = {}
    screens_by_key = {}
    plates_by_barcode = {}
    locations_by_key = {}

    for project in session.query(Project).all():
        projects_by_group[project.group_name] = project

    for screen in session.query(Screen).all():
        screens_by_key[(screen.project_id, screen.screen_number)] = screen

    for plate in session.query(Plate).all():
        plates_by_barcode[plate.barcode] = plate

    for location in session.query(Location).all():
        locations_by_key[(location.barcode_id, location.img_path, location.source_path)] = location

    cache = {
        "projects_by_group": projects_by_group,
        "screens_by_key": screens_by_key,
        "plates_by_barcode": plates_by_barcode,
        "locations_by_key": locations_by_key,
    }
    session.info["management_cache"] = cache
    return cache

def import_project(session, group_name, project_name=None):
    cache = _get_management_cache(session)
    project = cache["projects_by_group"].get(group_name)

    if project is None:
        project = session.query(Project).filter_by(group_name=group_name).first()

    if not project:
        project = Project(group_name=group_name, name=project_name)
        session.add(project)
        session.flush()
        cache["projects_by_group"][group_name] = project
    elif project_name and project.name != project_name:
        # Update name if a new one is provided and different
        project.name = project_name
        session.flush()
    return project


def import_screen(session, project, screen_number, description=None):
    cache = _get_management_cache(session)
    key = (project.id, screen_number)
    screen = cache["screens_by_key"].get(key)

    if screen is None:
        screen = session.query(Screen).filter_by(screen_number=screen_number, project=project).first()

    if screen:
        # Update the existing screen if it already exists
        screen.screen_description = description
    else:
        # Create a new screen if it doesn't exist
        screen = Screen(
            screen_number=screen_number,
            screen_description=description,
            project=project,
        )
        session.add(screen)

    session.flush()
    cache["screens_by_key"][key] = screen
    return screen


def import_plate(session, screen, name, barcode, date_experiment):
    if barcode is None or not str(barcode).strip():
        raise ValueError("Plate barcode is required")

    cache = _get_management_cache(session)
    plate = cache["plates_by_barcode"].get(barcode)

    if plate is None:
        plate = session.query(Plate).filter_by(barcode=barcode).first()

    if plate:
        # Update the existing plate if it already exists
        plate.name = name
        plate.date_experiment = str(date_experiment)
        plate.screen = screen

    else:
        # Create a new plate if it doesn't exist
        plate = Plate(name=name, barcode=barcode, date_experiment=str(date_experiment))
        screen.plates.append(plate)
        session.add(plate)
    session.flush()
    cache["plates_by_barcode"][barcode] = plate
    return plate


def import_location(session, plate, img_path, source_path):
    cache = _get_management_cache(session)
    key = (plate.id, img_path, source_path)
    location = cache["locations_by_key"].get(key)

    if location is None:
        location = session.query(Location).filter_by(
            barcode_id=plate.id,
            img_path=img_path,
            source_path=source_path,
        ).first()

    if not location:
        location = Location(
            img_path=img_path,
            source_path=source_path,
            plate=plate,
        )
        session.add(location)
        session.flush()
    cache["locations_by_key"][key] = location

    return location