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

import marshmallow
# IMPORTS ------------------------------------------------
from datetime import datetime
from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_wtf import FlaskForm

from app.datamgmt.case.case_db import case_get_desc_crc
from app.datamgmt.case.case_db import get_case
from app.datamgmt.case.case_notes_db import add_note
from app.datamgmt.case.case_notes_db import add_note_group
from app.datamgmt.case.case_notes_db import delete_note
from app.datamgmt.case.case_notes_db import delete_note_group
from app.datamgmt.case.case_notes_db import find_pattern_in_notes
from app.datamgmt.case.case_notes_db import get_group_details
from app.datamgmt.case.case_notes_db import get_groups_short
from app.datamgmt.case.case_notes_db import get_note
from app.datamgmt.case.case_notes_db import get_notes_from_group
from app.datamgmt.case.case_notes_db import update_note
from app.datamgmt.case.case_notes_db import update_note_group
from app.datamgmt.states import get_notes_state
from app.forms import CaseNoteForm
from app.iris_engine.module_handler.module_handler import call_modules_hook
from app.iris_engine.utils.tracker import track_activity
from app.schema.marshables import CaseAddNoteSchema
from app.schema.marshables import CaseGroupNoteSchema
from app.schema.marshables import CaseNoteSchema
from app.util import api_login_required
from app.util import login_required
from app.util import response_error
from app.util import response_success

case_notes_blueprint = Blueprint('case_notes',
                                 __name__,
                                 template_folder='templates')


# CONTENT ------------------------------------------------
@case_notes_blueprint.route('/case/notes', methods=['GET'])
@login_required
def case_notes(caseid, url_redir):
    if url_redir:
        return redirect(url_for('case_notes.case_notes', cid=caseid, redirect=True))

    form = FlaskForm()
    case = get_case(caseid)

    if case:
        crc32, desc = case_get_desc_crc(caseid)
    else:
        crc32 = None
        desc = None

    return render_template('case_notes.html', case=case, form=form, th_desc=desc, crc=crc32)


@case_notes_blueprint.route('/case/notes/<int:cur_id>', methods=['GET'])
@api_login_required
def case_note_detail(cur_id, caseid):
    try:
        note = get_note(cur_id, caseid=caseid)
        if not note:
            return response_error(msg="Invalid note ID")
        note_schema = CaseNoteSchema()

        return response_success(data=note_schema.dump(note))

    except marshmallow.exceptions.ValidationError as e:
        return response_error(msg="Data error", data=e.messages, status=400)


@case_notes_blueprint.route('/case/notes/<int:cur_id>/modal', methods=['GET'])
@login_required
def case_note_detail_modal(cur_id, caseid, url_redir):
    if url_redir:
        return redirect(url_for('case_notes.case_notes', cid=caseid, redirect=True))

    form = CaseNoteForm()

    note = get_note(cur_id, caseid)
    ca = None

    if note:
        form.content = note.note_content
        form.title = note.note_title
        form.note_title.render_kw = {"value": note.note_title}
        ca = note.custom_attributes

    return render_template("modal_note_edit.html", note=form, id=cur_id, attributes=ca)


@case_notes_blueprint.route('/case/notes/delete/<int:cur_id>', methods=['GET'])
@api_login_required
def case_note_delete(cur_id, caseid):

    call_modules_hook('on_preload_note_delete', data=cur_id, caseid=caseid)

    note = get_note(cur_id, caseid)
    if not note:
        return response_error("Invalid note ID for this case")

    try:

        delete_note(cur_id, caseid)

    except Exception as e:
        return response_error("Unable to remove note", data=e.__traceback__)

    call_modules_hook('on_postload_note_delete', data=cur_id, caseid=caseid)

    track_activity("deleted note ID {}".format(cur_id), caseid=caseid)
    return response_success("Note deleted {}".format(cur_id))


@case_notes_blueprint.route('/case/notes/update/<int:cur_id>', methods=['POST'])
@api_login_required
def case_note_save(cur_id, caseid):

    try:
        # validate before saving
        addnote_schema = CaseAddNoteSchema()

        request_data = call_modules_hook('on_preload_note_update', data=request.get_json(), caseid=caseid)

        request_data['note_id'] = cur_id
        addnote_schema.load(request_data, partial=['group_id'])

        note = update_note(note_content=request_data.get('note_content'),
                           note_title=request_data.get('note_title'),
                           update_date=datetime.utcnow(),
                           user_id=current_user.id,
                           note_id=cur_id,
                           caseid=caseid
                           )
        if not note:

            return response_error("Invalid note ID for this case")

        note = call_modules_hook('on_postload_note_update', data=note, caseid=caseid)

    except marshmallow.exceptions.ValidationError as e:
        return response_error(msg="Data error", data=e.messages, status=400)

    track_activity("updated note {}".format(request_data.get('note_title')), caseid=caseid)
    return response_success("Note ID {} saved".format(cur_id), data=addnote_schema.dump(note))


@case_notes_blueprint.route('/case/notes/add', methods=['POST'])
@api_login_required
def case_note_add(caseid):
    try:
        # validate before saving
        addnote_schema = CaseAddNoteSchema()
        request_data = call_modules_hook('on_preload_note_create', data=request.get_json(), caseid=caseid)

        addnote_schema.verify_group_id(request_data, caseid=caseid)
        addnote_schema.load(request_data)

        note = add_note(request_data.get('note_title'),
                        datetime.utcnow(),
                        current_user.id,
                        caseid,
                        request_data.get('group_id'),
                        note_content=request_data.get('note_content'))

        note = call_modules_hook('on_postload_note_create', data=note, caseid=caseid)

        if note:
            casenote_schema = CaseNoteSchema()
            track_activity("added note ID {}".format(note.note_id), caseid=caseid)
            return response_success('Note added', data=casenote_schema.dump(note))

        return response_error("Unable to create note for internal reasons")

    except marshmallow.exceptions.ValidationError as e:
        return response_error(msg="Data error", data=e.messages, status=400)


@case_notes_blueprint.route('/case/notes/groups/list', methods=['GET'])
@api_login_required
def case_load_notes_groups(caseid):

    if not get_case(caseid=caseid):
        return response_error("Invalid case ID")

    groups_short = get_groups_short(caseid)

    sta = []

    for group in groups_short:
        notes = get_notes_from_group(caseid=caseid, group_id=group.group_id)
        group_d = group._asdict()
        group_d['notes'] = [note._asdict() for note in notes]

        sta.append(group_d)

    sta = sorted(sta, key=lambda i: i['group_id'])

    ret = {
        'groups': sta,
        'state': get_notes_state(caseid=caseid)
    }

    return response_success("", data=ret)


@case_notes_blueprint.route('/case/notes/state', methods=['GET'])
@api_login_required
def case_notes_state(caseid):
    os = get_notes_state(caseid=caseid)
    if os:
        return response_success(data=os)
    else:
        return response_error('No notes state for this case.')


@case_notes_blueprint.route('/case/notes/search', methods=['POST'])
@api_login_required
def case_search_notes(caseid):

    if request.is_json:
        search = request.json.get('search_term')
        ns = []
        if search:
            search = "%{}%".format(search)
            ns = find_pattern_in_notes(search, caseid)

            ns = [row._asdict() for row in ns]

        return response_success("", data=ns)

    return response_error("Invalid request")


@case_notes_blueprint.route('/case/notes/groups/add', methods=['POST'])
@api_login_required
def case_add_notes_groups(caseid):
    title = ''
    if request.is_json:
        title = request.json.get('group_title') or ''

        ng = add_note_group(group_title=title,
                            caseid=caseid,
                            userid=current_user.id,
                            creationdate=datetime.utcnow())

        if ng.group_id:
            group_schema = CaseGroupNoteSchema()
            track_activity("added group note ID {}".format(ng.group_id), caseid=caseid)

            return response_success("Notes group added", data=group_schema.dump(ng))

        else:
            return response_error("Unable to add a new group")

    return response_error("Invalid request")


@case_notes_blueprint.route('/case/notes/groups/delete/<int:cur_id>', methods=['GET'])
@api_login_required
def case_delete_notes_groups(cur_id, caseid):

    if not delete_note_group(cur_id, caseid):
        return response_error("Invalid group ID")

    track_activity("deleted group note ID {}".format(cur_id), caseid=caseid)

    return response_success("Group ID {} deleted".format(cur_id))


@case_notes_blueprint.route('/case/notes/groups/<int:cur_id>', methods=['GET'])
@api_login_required
def case_get_notes_group(cur_id, caseid):

    group = get_group_details(cur_id, caseid)
    if not group:
        return response_error(f"Group ID {cur_id} not found")

    return response_success("", data=group)


@case_notes_blueprint.route('/case/notes/groups/update/<int:cur_id>', methods=['POST'])
@api_login_required
def case_edit_notes_groups(cur_id, caseid):

    js_data = request.get_json()
    if not js_data:
        return response_error("Invalid data")

    group_title = js_data.get('group_title')
    if not group_title:
        return response_error("Missing field group_title")

    ng = update_note_group(group_title, cur_id, caseid)

    if ng:
        # Note group has been properly found and updated in db
        track_activity("updated group note {}".format(group_title), caseid=caseid)
        group_schema = CaseGroupNoteSchema()
        return response_success("Updated title of group ID {}".format(cur_id), data=group_schema.dump(ng))

    return response_error("Group ID {} not found".format(cur_id))

