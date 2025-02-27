#!/usr/bin/env python3
#
#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS)
#  ir@cyberactionlab.net
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# IMPORTS ------------------------------------------------
import secrets

from flask_login import UserMixin
from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import Sequence
from sqlalchemy import String
from sqlalchemy import TIMESTAMP
from sqlalchemy import Text
from sqlalchemy import create_engine
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from app import app
from app import db

Base = declarative_base()
metadata = Base.metadata


def create_safe(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return False
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return True


def get_by_value_or_create(session, model, fieldname, **kwargs):
    select_value = {fieldname: kwargs.get(fieldname)}
    instance = session.query(model).filter_by(**select_value).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


# CONTENT ------------------------------------------------
class Client(db.Model):
    __tablename__ = 'client'

    client_id = Column(Integer, primary_key=True)
    name = Column(String(2048), unique=True)
    custom_attributes = Column(JSON)


class AssetsType(db.Model):
    __tablename__ = 'assets_type'

    asset_id = Column(Integer, primary_key=True)
    asset_name = Column(String(155))
    asset_description = Column(String(255))
    asset_icon_not_compromised = Column(String(255))
    asset_icon_compromised = Column(String(255))


class CaseAssets(db.Model):
    __tablename__ = 'case_assets'

    asset_id = Column(Integer, primary_key=True)
    asset_name = Column(Text)
    asset_description = Column(Text)
    asset_domain = Column(Text)
    asset_ip = Column(Text)
    asset_info = Column(Text)
    asset_compromised = Column(Boolean)
    asset_type_id = Column(ForeignKey('assets_type.asset_id'))
    asset_tags = Column(Text)
    case_id = Column(ForeignKey('cases.case_id'))
    date_added = Column(DateTime)
    date_update = Column(DateTime)
    user_id = Column(ForeignKey('user.id'))
    analysis_status_id = Column(ForeignKey('analysis_status.id'))
    custom_attributes = Column(JSON)

    case = relationship('Cases')
    user = relationship('User')
    asset_type = relationship('AssetsType')
    analysis_status = relationship('AnalysisStatus')


class AnalysisStatus(db.Model):
    __tablename__ = 'analysis_status'

    id = Column(Integer, primary_key=True)
    name = Column(Text)


class CaseEventsAssets(db.Model):
    __tablename__ = 'case_events_assets'

    id = Column(Integer, primary_key=True)
    event_id = Column(ForeignKey('cases_events.event_id'))
    asset_id = Column(ForeignKey('case_assets.asset_id'))
    case_id = Column(ForeignKey('cases.case_id'))

    event = relationship('CasesEvent')
    asset = relationship('CaseAssets')
    case = relationship('Cases')


class CaseEventsIoc(db.Model):
    __tablename__ = 'case_events_ioc'

    id = Column(Integer, primary_key=True)
    event_id = Column(ForeignKey('cases_events.event_id'))
    ioc_id = Column(ForeignKey('ioc.ioc_id'))
    case_id = Column(ForeignKey('cases.case_id'))

    event = relationship('CasesEvent')
    ioc = relationship('Ioc')
    case = relationship('Cases')


class ObjectState(db.Model):
    object_id = Column(Integer, primary_key=True)
    object_case_id = Column(ForeignKey('cases.case_id'))
    object_updated_by_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    object_name = Column(Text)
    object_state = Column(BigInteger)
    object_last_update = Column(TIMESTAMP)

    case = relationship('Cases')
    updated_by = relationship('User')


class EventCategory(db.Model):
    __tablename__ = 'event_category'

    id = Column(Integer, primary_key=True)
    name = Column(Text)


class CaseEventCategory(db.Model):
    __tablename__ = 'case_events_category'

    id = Column(Integer, primary_key=True)
    event_id = Column(ForeignKey('cases_events.event_id'), unique=True)
    category_id = Column(ForeignKey('event_category.id'))

    event = relationship('CasesEvent', cascade="delete")
    category = relationship('EventCategory')


class CaseGraphAssets(db.Model):
    __tablename__ = 'case_graph_assets'

    id = Column(Integer, primary_key=True)
    case_id = Column(ForeignKey('cases.case_id'))
    asset_id = Column(Integer)
    asset_type_id = Column(ForeignKey('assets_type.asset_id'))

    case = relationship('Cases')
    asset_type = relationship('AssetsType')


class CaseGraphLinks(db.Model):
    __tablename__ = 'case_graph_links'

    id = Column(Integer, primary_key=True)
    case_id = Column(ForeignKey('cases.case_id'))
    source_id = Column(ForeignKey('case_graph_assets.id'))
    dest_id = Column(ForeignKey('case_graph_assets.id'))

    case = relationship('Cases')


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


class Languages(db.Model):
    __tablename__ = 'languages'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), unique=True)
    code = db.Column(db.String(), unique=True)


class ReportType(db.Model):
    __tablename__ = 'report_type'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Text(), unique=True)


class CaseTemplateReport(db.Model):
    __tablename__ = 'case_template_report'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    description = db.Column(db.String())
    internal_reference = db.Column(db.String(), unique=True)
    naming_format = db.Column(db.String())
    created_by_user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    date_created = db.Column(DateTime)
    language_id = db.Column(db.Integer(), db.ForeignKey('languages.id'))
    report_type_id = db.Column(db.Integer(), db.ForeignKey('report_type.id'))

    report_type = relationship('ReportType')
    language = relationship('Languages')
    created_by_user = relationship('User')


# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(64), unique=True)
    name = db.Column(db.String(64), unique=False)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(500))
    ctx_case = db.Column(Integer)
    ctx_human_case = db.Column(db.String(256))
    active = db.Column(db.Boolean())
    api_key = db.Column(db.Text(), unique=True)
    in_dark_mode = db.Column(db.Boolean())

    roles = db.relationship('Role', secondary='user_roles')

    def __init__(self, user, name, email, password, active):
        self.user = user
        self.name = name
        self.password = password
        self.email = email
        self.active = active
        self.roles = []

    def __repr__(self):
        return str(self.id) + ' - ' + str(self.user)

    def save(self):

        # Default roles:
        roles = Role.query.filter(or_(Role.id == 2, Role.id == 3)).all()
        self.roles = roles

        self.api_key = secrets.token_urlsafe(nbytes=64)

        # inject self into db session
        db.session.add(self)
        db.session.commit()

        for role in roles:
            ur = UserRoles()
            ur.user_id = self.id
            ur.role_id = role.id
            db.session.add(ur)

        # commit change and save the object
        db.session.commit()

        return self

    def is_admin(self):
        roles = [role.name for role in self.roles]
        if "administrator" in roles:
            return True
        return False


class Tlp(db.Model):
    __tablename__ = 'tlp'

    tlp_id = Column(Integer, primary_key=True)
    tlp_name = Column(Text)
    tlp_bscolor = Column(Text)


class Ioc(db.Model):
    __tablename__ = 'ioc'

    ioc_id = Column(Integer, primary_key=True)
    ioc_value = Column(Text)
    ioc_type_id = Column(ForeignKey('ioc_type.type_id'))
    ioc_description = Column(Text)
    ioc_tags = Column(String(512))
    user_id = Column(ForeignKey('user.id'))
    ioc_misp = Column(Text)
    ioc_tlp_id = Column(ForeignKey('tlp.tlp_id'))
    custom_attributes = Column(JSON)

    user = relationship('User')
    tlp = relationship('Tlp')
    ioc_type = relationship('IocType')


class CustomAttribute(db.Model):
    __tablename__ = 'custom_attribute'

    attribute_id = Column(Integer, primary_key=True)
    attribute_display_name = Column(Text)
    attribute_description = Column(Text)
    attribute_for = Column(Text)
    attribute_content = Column(JSON)


class IocType(db.Model):
    __tablename__ = 'ioc_type'

    type_id = Column(Integer, primary_key=True)
    type_name = Column(Text)
    type_description = Column(Text)
    type_taxonomy = Column(Text)


class IocLink(db.Model):
    __tablename__ = 'ioc_link'

    ioc_link_id = Column(Integer, primary_key=True)
    ioc_id = Column(ForeignKey('ioc.ioc_id'))
    case_id = Column(ForeignKey('cases.case_id'), nullable=False)

    ioc = relationship('Ioc')
    case = relationship('Cases')


class IocAssetLink(db.Model):
    __tablename__ = 'ioc_asset_link'

    ioc_asset_link_id = Column(Integer, primary_key=True)
    ioc_id = Column(ForeignKey('ioc.ioc_id'), nullable=False)
    asset_id = Column(ForeignKey('case_assets.asset_id'), nullable=False)

    ioc = relationship('Ioc')
    asset = relationship('CaseAssets')


class OsType(db.Model):
    __tablename__ = 'os_type'

    type_id = Column(Integer, primary_key=True)
    type_name = Column(String(155))


class CasesAssetsExt(db.Model):
    __tablename__ = 'cases_assets_ext'

    asset_id = Column(Integer, primary_key=True)
    type_id = Column(ForeignKey('assets_type.asset_id'))
    case_id = Column(ForeignKey('cases.case_id'))
    asset_content = Column(Text)

    type = relationship('AssetsType')
    case = relationship('Cases')


class Notes(db.Model):
    __tablename__ = 'notes'

    note_id = Column(Integer, primary_key=True)
    note_title = Column(String(155))
    note_content = Column(Text)
    note_user = Column(ForeignKey('user.id'))
    note_creationdate = Column(DateTime)
    note_lastupdate = Column(DateTime)
    note_case_id = Column(ForeignKey('cases.case_id'))
    custom_attributes = Column(JSON)

    user = relationship('User')
    case = relationship('Cases')


class NotesGroup(db.Model):
    __tablename__ = 'notes_group'

    group_id = Column(Integer, primary_key=True)
    group_title = Column(String(155))
    group_user = Column(ForeignKey('user.id'))
    group_creationdate = Column(DateTime)
    group_lastupdate = Column(DateTime)
    group_case_id = Column(ForeignKey('cases.case_id'))

    user = relationship('User')
    case = relationship('Cases')


class NotesGroupLink(db.Model):
    __tablename__ = 'notes_group_link'

    link_id = Column(Integer, primary_key=True)
    group_id = Column(ForeignKey('notes_group.group_id'))
    note_id = Column(ForeignKey('notes.note_id'))
    case_id = Column(ForeignKey('cases.case_id'))

    note = relationship('Notes')
    note_group = relationship('NotesGroup')
    case = relationship('Cases')


class CaseKanban(db.Model):
    __tablename__ = 'case_kanban'

    case_id = Column(ForeignKey('cases.case_id'), primary_key=True)
    kanban_data = Column(Text)

    case = relationship('Cases')


class CaseReceivedFile(db.Model):
    __tablename__ = 'case_received_file'

    id = Column(Integer, primary_key=True)
    filename = Column(Text)
    date_added = Column(DateTime)
    file_hash = Column(String(65))
    file_description = Column(Text)
    file_size = Column(BigInteger)
    case_id = Column(ForeignKey('cases.case_id'))
    user_id = Column(ForeignKey('user.id'))
    custom_attributes = Column(JSON)

    case = relationship('Cases')
    user = relationship('User')


class TaskStatus(db.Model):
    __tablename__ = 'task_status'

    id = Column(Integer, primary_key=True)
    status_name = Column(Text)
    status_description = Column(Text)
    status_bscolor = Column(Text)


class CaseTasks(db.Model):
    __tablename__ = 'case_tasks'

    id = Column(Integer, primary_key=True)
    task_title = Column(Text)
    task_description = Column(Text)
    task_tags = Column(Text)
    task_open_date = Column(DateTime)
    task_close_date = Column(DateTime)
    task_last_update = Column(DateTime)
    task_userid_open = Column(ForeignKey('user.id'))
    task_userid_close = Column(ForeignKey('user.id'))
    task_userid_update = Column(ForeignKey('user.id'))
    task_assignee_id = Column(ForeignKey('user.id'))
    task_status_id = Column(ForeignKey('task_status.id'))
    task_case_id = Column(ForeignKey('cases.case_id'))
    custom_attributes = Column(JSON)

    case = relationship('Cases')
    user_open = relationship('User', foreign_keys=[task_userid_open])
    user_close = relationship('User', foreign_keys=[task_userid_close])
    user_update = relationship('User', foreign_keys=[task_userid_update])
    user_assigned = relationship('User', foreign_keys=[task_assignee_id])
    status = relationship('TaskStatus', foreign_keys=[task_status_id])


class GlobalTasks(db.Model):
    __tablename__ = 'global_tasks'

    id = Column(Integer, primary_key=True)
    task_title = Column(Text)
    task_description = Column(Text)
    task_tags = Column(Text)
    task_open_date = Column(DateTime)
    task_close_date = Column(DateTime)
    task_last_update = Column(DateTime)
    task_userid_open = Column(ForeignKey('user.id'))
    task_userid_close = Column(ForeignKey('user.id'))
    task_userid_update = Column(ForeignKey('user.id'))
    task_assignee_id = Column(ForeignKey('user.id'), nullable=True)
    task_status_id = Column(ForeignKey('task_status.id'))

    user_open = relationship('User', foreign_keys=[task_userid_open])
    user_close = relationship('User', foreign_keys=[task_userid_close])
    user_update = relationship('User', foreign_keys=[task_userid_update])
    user_assigned = relationship('User', foreign_keys=[task_assignee_id])
    status = relationship('TaskStatus', foreign_keys=[task_status_id])


class UserActivity(db.Model):
    __tablename__ = "user_activity"

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('user.id'), nullable=True)
    case_id = Column(ForeignKey('cases.case_id'), nullable=True)
    activity_date = Column(DateTime)
    activity_desc = Column(Text)
    user_input = Column(Boolean)
    is_from_api = Column(Boolean)

    user = relationship('User')
    case = relationship('Cases')


class ServerSettings(db.Model):
    __table_name__ = "server_settings"

    id = Column(Integer, primary_key=True)
    https_proxy = Column(Text)
    http_proxy = Column(Text)
    prevent_post_mod_repush = Column(Boolean)
    has_updates_available = Column(Boolean)
    enable_updates_check = Column(Boolean)


class IrisModule(db.Model):
    __tablename__ = "iris_module"

    id = Column(Integer, primary_key=True)
    added_by_id = Column(ForeignKey('user.id'), nullable=False)
    module_human_name = Column(Text)
    module_name = Column(Text)
    module_description = Column(Text)
    module_version = Column(Text)
    interface_version = Column(Text)
    date_added = Column(DateTime)
    is_active = Column(Boolean)
    has_pipeline = Column(Boolean)
    pipeline_args = Column(JSON)
    module_config = Column(JSON)
    module_type = Column(Text)

    user = relationship('User')


class IrisHook(db.Model):
    __tablename__ = "iris_hooks"

    id = Column(Integer, primary_key=True)
    hook_name = Column(Text)
    hook_description = Column(Text)


class IrisModuleHook(db.Model):
    __tablename__ = "iris_module_hooks"

    id = Column(Integer, primary_key=True)
    module_id = Column(ForeignKey('iris_module.id'), nullable=False)
    hook_id = Column(ForeignKey('iris_hooks.id'), nullable=False)
    is_manual_hook = Column(Boolean)
    manual_hook_ui_name = Column(Text)
    retry_on_fail = Column(Boolean)
    max_retry = Column(Integer)
    run_asynchronously = Column(Boolean)
    wait_till_return = Column(Boolean)

    module = relationship('IrisModule')
    hook = relationship('IrisHook')


class IrisReport(db.Model):
    __tablename__ = 'iris_reports'

    report_id = Column(db.Integer,Sequence("iris_reports_id_seq"), primary_key=True)
    case_id = Column(ForeignKey('cases.case_id'), nullable=False)
    report_title = Column(String(155))
    report_date = Column(DateTime)
    report_content = Column('report_content', JSON)
    user_id = Column(ForeignKey('user.id'))

    user = relationship('User')
    case = relationship('Cases')

    def __init__(self, case_id, report_title, report_date, report_content, user_id):
        self.case_id = case_id
        self.report_title = report_title
        self.report_date = report_date
        self.report_content = report_content
        self.user_id = user_id

    def save(self):
        # Create an engine and a session because this method
        # will be called from Celery thread and might cause
        # error if it uses the session context of the app
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        Session = sessionmaker(bind=engine)
        session = Session()

        # inject self into db session
        session.add(self)

        # commit change and save the object
        session.commit()

        # Close session
        session.close()

        # Dispose engine
        engine.dispose()

        return self


class CeleryTaskMeta(db.Model):
    __bind_key__ = 'iris_tasks'
    __tablename__ = 'celery_taskmeta'

    id = Column(Integer, Sequence('task_id_sequence'), primary_key=True)
    task_id = Column(String(155))
    status = Column(String(50))
    result = Column(LargeBinary)
    date_done = Column(DateTime)
    traceback = Column(Text)
    name = Column(String(155))
    args = Column(LargeBinary)
    kwargs = Column(LargeBinary)
    worker = Column(String(155))
    retries = Column(Integer)
    queue = Column(String(155))


def create_safe_attr(session, attribute_display_name, attribute_description, attribute_for, attribute_content):
    cat = CustomAttribute.query.filter(
        CustomAttribute.attribute_display_name == attribute_display_name,
        CustomAttribute.attribute_description == attribute_description,
        CustomAttribute.attribute_for == attribute_for
    ).first()

    if cat:
        return False
    else:
        instance = CustomAttribute()
        instance.attribute_display_name = attribute_display_name
        instance.attribute_description = attribute_description
        instance.attribute_for = attribute_for
        instance.attribute_content = attribute_content
        session.add(instance)
        session.commit()
        return True
