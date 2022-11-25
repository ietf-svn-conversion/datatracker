# Generated by Django 2.2.28 on 2022-06-21 11:44
#
# Important: To avoid corrupting timestamps in the database, do not use this migration as a dependency for
# future migrations. Use 0003_pause_to_change_use_tz instead.
#
import datetime

from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import migrations, connection

# to generate the expected columns list:
#
# from django.db import connection
# from pprint import pp
# cursor = connection.cursor()
# cursor.execute("""
# SELECT table_name, column_name
#     FROM information_schema.columns
#         WHERE table_schema='ietf_utf8'
#             AND column_type LIKE 'datetime%'
#             AND NOT table_name LIKE 'django_celery_beat_%'
#         ORDER BY table_name, column_name;
# """)
# pp(cursor.fetchall())
#
expected_datetime_columns = (
    ('auth_user', 'date_joined'),
    ('auth_user', 'last_login'),
    ('community_documentchangedates', 'new_version_date'),
    ('community_documentchangedates', 'normal_change_date'),
    ('community_documentchangedates', 'significant_change_date'),
    ('django_admin_log', 'action_time'),
    ('django_migrations', 'applied'),
    ('django_session', 'expire_date'),
    ('doc_ballotpositiondocevent', 'comment_time'),
    ('doc_ballotpositiondocevent', 'discuss_time'),
    ('doc_deletedevent', 'time'),
    ('doc_docevent', 'time'),
    ('doc_dochistory', 'expires'),
    ('doc_dochistory', 'time'),
    ('doc_docreminder', 'due'),
    ('doc_document', 'expires'),
    ('doc_document', 'time'),
    ('doc_documentactionholder', 'time_added'),
    ('doc_initialreviewdocevent', 'expires'),
    ('doc_irsgballotdocevent', 'duedate'),
    ('doc_lastcalldocevent', 'expires'),
    ('group_group', 'time'),
    ('group_groupevent', 'time'),
    ('group_grouphistory', 'time'),
    ('group_groupmilestone', 'time'),
    ('group_groupmilestonehistory', 'time'),
    ('ipr_iprdisclosurebase', 'time'),
    ('ipr_iprevent', 'response_due'),
    ('ipr_iprevent', 'time'),
    ('liaisons_liaisonstatementevent', 'time'),
    ('mailinglists_subscribed', 'time'),
    ('mailinglists_allowlisted', 'time'),
    ('meeting_floorplan', 'modified'),
    ('meeting_room', 'modified'),
    ('meeting_schedtimesessassignment', 'modified'),
    ('meeting_schedulingevent', 'time'),
    ('meeting_session', 'modified'),
    ('meeting_session', 'scheduled'),
    ('meeting_slidesubmission', 'time'),
    ('meeting_timeslot', 'modified'),
    ('meeting_timeslot', 'time'),
    ('message_message', 'sent'),
    ('message_message', 'time'),
    ('message_sendqueue', 'send_at'),
    ('message_sendqueue', 'sent_at'),
    ('message_sendqueue', 'time'),
    ('nomcom_feedback', 'time'),
    ('nomcom_feedbacklastseen', 'time'),
    ('nomcom_nomination', 'time'),
    ('nomcom_nomineeposition', 'time'),
    ('nomcom_topicfeedbacklastseen', 'time'),
    ('oidc_provider_code', 'expires_at'),
    ('oidc_provider_token', 'expires_at'),
    ('oidc_provider_userconsent', 'date_given'),
    ('oidc_provider_userconsent', 'expires_at'),
    ('person_email', 'time'),
    ('person_historicalemail', 'history_date'),
    ('person_historicalemail', 'time'),
    ('person_historicalperson', 'history_date'),
    ('person_historicalperson', 'time'),
    ('person_person', 'time'),
    ('person_personalapikey', 'created'),
    ('person_personalapikey', 'latest'),
    ('person_personevent', 'time'),
    ('request_profiler_profilingrecord', 'end_ts'),
    ('request_profiler_profilingrecord', 'start_ts'),
    ('review_historicalreviewassignment', 'assigned_on'),
    ('review_historicalreviewassignment', 'completed_on'),
    ('review_historicalreviewassignment', 'history_date'),
    ('review_historicalreviewersettings', 'history_date'),
    ('review_historicalreviewrequest', 'history_date'),
    ('review_historicalreviewrequest', 'time'),
    ('review_historicalunavailableperiod', 'history_date'),
    ('review_reviewassignment', 'assigned_on'),
    ('review_reviewassignment', 'completed_on'),
    ('review_reviewrequest', 'time'),
    ('review_reviewwish', 'time'),
    ('south_migrationhistory', 'applied'),
    ('submit_preapproval', 'time'),
    ('submit_submissioncheck', 'time'),
    ('submit_submissionevent', 'time'),
    ('tastypie_apikey', 'created'),
    ('utils_versioninfo', 'time'),
)

def convert_pre1970_timestamps(apps, schema_editor):
    """Convert timestamps that CONVERT_TZ cannot handle

    This could be made to do the entire conversion but some tables that require converison
    do not use 'id' as their PK. Rather than reinvent the ORM, we'll let SQL do what it can
    with CONVERT_TZ and clean up after. The tables that have pre-1970 timestamps both have
    'id' columns.
    """
    min_timestamp = "1969-12-31 16:00:01"  # minimum PST8PDT timestamp CONVERT_TZ can convert to UTC
    with connection.cursor() as cursor:
        # To get these values, use:
        # convert_manually = [
        #     (tbl, col) for (tbl, col) in expected_datetime_columns
        #     if cursor.execute(
        #         f'SELECT COUNT(*) FROM {tbl} WHERE {col} IS NOT NULL AND {col} <= %s',
        #         (min_timestamp,)
        #     ) and cursor.fetchone()[0] > 0
        # ]
        convert_manually = [('doc_docevent', 'time'), ('group_groupevent', 'time')]
        pst8pdt = ZoneInfo('PST8PDT')
        for (tbl, col) in convert_manually:
            cursor.execute(f'SELECT id, {col} FROM {tbl} WHERE {col} < %s', (min_timestamp,))
            for (id, naive_in_pst8pdt) in cursor.fetchall():
                aware_in_pst8pdt = naive_in_pst8pdt.replace(tzinfo=pst8pdt)
                aware_in_utc = aware_in_pst8pdt.astimezone(datetime.timezone.utc)
                naive_in_utc = aware_in_utc.replace(tzinfo=None)
                cursor.execute(
                    f'UPDATE {tbl} SET {col}=%s WHERE id=%s',
                    (naive_in_utc, id)
                )


def forward(apps, schema_editor):
    # Check that the USE_TZ has been False so far, otherwise we might be corrupting timestamps. If this test
    # fails, be sure that no timestamps have been set since changing USE_TZ to True before re-running!
    assert not getattr(settings, 'USE_TZ', False), 'must keep USE_TZ = False until after this migration'

    # Check that we can safely ignore celery beat columns - it defaults to UTC if CELERY_TIMEZONE is not set.
    celery_timezone = getattr(settings, 'CELERY_TIMEZONE', None)
    assert celery_timezone in ('UTC', None), 'update migration, celery is not using UTC'
    # If the CELERY_ENABLE_UTC flag is set, abort because someone is using a strange configuration.
    assert not hasattr(settings, 'CELERY_ENABLE_UTC'), 'update migration, settings.CELERY_ENABLE_UTC was not expected'

    with connection.cursor() as cursor:
        # Check that we have timezones.
        # If these assertions fail, the DB does not know all the necessary time zones.
        # To load timezones,
        #   $ mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root mysql
        # (on a dev system, first connect to the db image with `docker compose exec db bash`)
        cursor.execute("SELECT CONVERT_TZ('2022-06-22T17:43:00', 'PST8PDT', 'UTC');")
        assert not any(None in row for row in cursor.fetchall()), 'database does not recognize PST8PDT'
        cursor.execute(
            "SELECT CONVERT_TZ('2022-06-22T17:43:00', time_zone, 'UTC') FROM meeting_meeting WHERE time_zone != '';"
        )
        assert not any(None in row for row in cursor.fetchall()), 'database does not recognize a meeting time zone'

        # Check that we have all and only the expected datetime columns to work with.
        # If this fails, figure out what changed and decide how to proceed safely.
        cursor.execute("""
        SELECT table_name, column_name 
            FROM information_schema.columns 
                WHERE table_schema='ietf_utf8' 
                    AND column_type LIKE 'datetime%'
                    AND NOT table_name LIKE 'django_celery_beat_%' 
                    AND NOT table_name='utils_dumpinfo'
                ORDER BY table_name, column_name;
        """)
        assert cursor.fetchall() == expected_datetime_columns, 'unexpected or missing datetime columns in db'


class Migration(migrations.Migration):
    dependencies = [
        ('doc', '0046_use_timezone_now_for_doc_models'),
        ('group', '0059_use_timezone_now_for_group_models'),
        ('meeting', '0058_meeting_time_zone_not_blank'),
        ('message', '0012_use_timezone_now_for_message_models'),
        ('person', '0029_use_timezone_now_for_person_models'),
        ('review', '0029_use_timezone_now_for_review_models'),
        ('submit', '0011_use_timezone_now_for_submit_models'),
        ('utils', '0001_initial'),
    ]

    # To generate the queries:
    #
    # min_timestamp = "1969-12-31 16:00:01"  # minimum PST8PDT timestamp CONVERT_TZ can convert to UTC
    # pst8pdt_columns = [e for e in expected_datetime_columns if e != ('meeting_timeslot', 'time')]
    # queries = []
    # for table, column in pst8pdt_columns:
    #     queries.append(f"UPDATE {table} SET {column} = CONVERT_TZ({column}, 'PST8PDT', 'UTC') WHERE {column} >= '{min_timestamp}'";)
    #
    # queries.append("""
    # UPDATE meeting_timeslot
    #   JOIN meeting_meeting
    #     ON meeting_meeting.id = meeting_id
    #   SET time = CONVERT_TZ(time, time_zone, 'UTC');
    # """)
    #
    # print("\n".join(queries))
    #
    operations = [
        migrations.RunPython(forward),
        migrations.RunSQL("""
UPDATE auth_user SET date_joined = CONVERT_TZ(date_joined, 'PST8PDT', 'UTC') WHERE date_joined >= '1969-12-31 16:00:01';
UPDATE auth_user SET last_login = CONVERT_TZ(last_login, 'PST8PDT', 'UTC') WHERE last_login >= '1969-12-31 16:00:01';
UPDATE community_documentchangedates SET new_version_date = CONVERT_TZ(new_version_date, 'PST8PDT', 'UTC') WHERE new_version_date >= '1969-12-31 16:00:01';
UPDATE community_documentchangedates SET normal_change_date = CONVERT_TZ(normal_change_date, 'PST8PDT', 'UTC') WHERE normal_change_date >= '1969-12-31 16:00:01';
UPDATE community_documentchangedates SET significant_change_date = CONVERT_TZ(significant_change_date, 'PST8PDT', 'UTC') WHERE significant_change_date >= '1969-12-31 16:00:01';
UPDATE django_admin_log SET action_time = CONVERT_TZ(action_time, 'PST8PDT', 'UTC') WHERE action_time >= '1969-12-31 16:00:01';
UPDATE django_migrations SET applied = CONVERT_TZ(applied, 'PST8PDT', 'UTC') WHERE applied >= '1969-12-31 16:00:01';
UPDATE django_session SET expire_date = CONVERT_TZ(expire_date, 'PST8PDT', 'UTC') WHERE expire_date >= '1969-12-31 16:00:01';
UPDATE doc_ballotpositiondocevent SET comment_time = CONVERT_TZ(comment_time, 'PST8PDT', 'UTC') WHERE comment_time >= '1969-12-31 16:00:01';
UPDATE doc_ballotpositiondocevent SET discuss_time = CONVERT_TZ(discuss_time, 'PST8PDT', 'UTC') WHERE discuss_time >= '1969-12-31 16:00:01';
UPDATE doc_deletedevent SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE doc_docevent SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE doc_dochistory SET expires = CONVERT_TZ(expires, 'PST8PDT', 'UTC') WHERE expires >= '1969-12-31 16:00:01';
UPDATE doc_dochistory SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE doc_docreminder SET due = CONVERT_TZ(due, 'PST8PDT', 'UTC') WHERE due >= '1969-12-31 16:00:01';
UPDATE doc_document SET expires = CONVERT_TZ(expires, 'PST8PDT', 'UTC') WHERE expires >= '1969-12-31 16:00:01';
UPDATE doc_document SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE doc_documentactionholder SET time_added = CONVERT_TZ(time_added, 'PST8PDT', 'UTC') WHERE time_added >= '1969-12-31 16:00:01';
UPDATE doc_initialreviewdocevent SET expires = CONVERT_TZ(expires, 'PST8PDT', 'UTC') WHERE expires >= '1969-12-31 16:00:01';
UPDATE doc_irsgballotdocevent SET duedate = CONVERT_TZ(duedate, 'PST8PDT', 'UTC') WHERE duedate >= '1969-12-31 16:00:01';
UPDATE doc_lastcalldocevent SET expires = CONVERT_TZ(expires, 'PST8PDT', 'UTC') WHERE expires >= '1969-12-31 16:00:01';
UPDATE group_group SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE group_groupevent SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE group_grouphistory SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE group_groupmilestone SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE group_groupmilestonehistory SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE ipr_iprdisclosurebase SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE ipr_iprevent SET response_due = CONVERT_TZ(response_due, 'PST8PDT', 'UTC') WHERE response_due >= '1969-12-31 16:00:01';
UPDATE ipr_iprevent SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE liaisons_liaisonstatementevent SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE mailinglists_subscribed SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE mailinglists_allowlisted SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE meeting_floorplan SET modified = CONVERT_TZ(modified, 'PST8PDT', 'UTC') WHERE modified >= '1969-12-31 16:00:01';
UPDATE meeting_room SET modified = CONVERT_TZ(modified, 'PST8PDT', 'UTC') WHERE modified >= '1969-12-31 16:00:01';
UPDATE meeting_schedtimesessassignment SET modified = CONVERT_TZ(modified, 'PST8PDT', 'UTC') WHERE modified >= '1969-12-31 16:00:01';
UPDATE meeting_schedulingevent SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE meeting_session SET modified = CONVERT_TZ(modified, 'PST8PDT', 'UTC') WHERE modified >= '1969-12-31 16:00:01';
UPDATE meeting_session SET scheduled = CONVERT_TZ(scheduled, 'PST8PDT', 'UTC') WHERE scheduled >= '1969-12-31 16:00:01';
UPDATE meeting_slidesubmission SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE meeting_timeslot SET modified = CONVERT_TZ(modified, 'PST8PDT', 'UTC') WHERE modified >= '1969-12-31 16:00:01';
UPDATE message_message SET sent = CONVERT_TZ(sent, 'PST8PDT', 'UTC') WHERE sent >= '1969-12-31 16:00:01';
UPDATE message_message SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE message_sendqueue SET send_at = CONVERT_TZ(send_at, 'PST8PDT', 'UTC') WHERE send_at >= '1969-12-31 16:00:01';
UPDATE message_sendqueue SET sent_at = CONVERT_TZ(sent_at, 'PST8PDT', 'UTC') WHERE sent_at >= '1969-12-31 16:00:01';
UPDATE message_sendqueue SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE nomcom_feedback SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE nomcom_feedbacklastseen SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE nomcom_nomination SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE nomcom_nomineeposition SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE nomcom_topicfeedbacklastseen SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE oidc_provider_code SET expires_at = CONVERT_TZ(expires_at, 'PST8PDT', 'UTC') WHERE expires_at >= '1969-12-31 16:00:01';
UPDATE oidc_provider_token SET expires_at = CONVERT_TZ(expires_at, 'PST8PDT', 'UTC') WHERE expires_at >= '1969-12-31 16:00:01';
UPDATE oidc_provider_userconsent SET date_given = CONVERT_TZ(date_given, 'PST8PDT', 'UTC') WHERE date_given >= '1969-12-31 16:00:01';
UPDATE oidc_provider_userconsent SET expires_at = CONVERT_TZ(expires_at, 'PST8PDT', 'UTC') WHERE expires_at >= '1969-12-31 16:00:01';
UPDATE person_email SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE person_historicalemail SET history_date = CONVERT_TZ(history_date, 'PST8PDT', 'UTC') WHERE history_date >= '1969-12-31 16:00:01';
UPDATE person_historicalemail SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE person_historicalperson SET history_date = CONVERT_TZ(history_date, 'PST8PDT', 'UTC') WHERE history_date >= '1969-12-31 16:00:01';
UPDATE person_historicalperson SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE person_person SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE person_personalapikey SET created = CONVERT_TZ(created, 'PST8PDT', 'UTC') WHERE created >= '1969-12-31 16:00:01';
UPDATE person_personalapikey SET latest = CONVERT_TZ(latest, 'PST8PDT', 'UTC') WHERE latest >= '1969-12-31 16:00:01';
UPDATE person_personevent SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE request_profiler_profilingrecord SET end_ts = CONVERT_TZ(end_ts, 'PST8PDT', 'UTC') WHERE end_ts >= '1969-12-31 16:00:01';
UPDATE request_profiler_profilingrecord SET start_ts = CONVERT_TZ(start_ts, 'PST8PDT', 'UTC') WHERE start_ts >= '1969-12-31 16:00:01';
UPDATE review_historicalreviewassignment SET assigned_on = CONVERT_TZ(assigned_on, 'PST8PDT', 'UTC') WHERE assigned_on >= '1969-12-31 16:00:01';
UPDATE review_historicalreviewassignment SET completed_on = CONVERT_TZ(completed_on, 'PST8PDT', 'UTC') WHERE completed_on >= '1969-12-31 16:00:01';
UPDATE review_historicalreviewassignment SET history_date = CONVERT_TZ(history_date, 'PST8PDT', 'UTC') WHERE history_date >= '1969-12-31 16:00:01';
UPDATE review_historicalreviewersettings SET history_date = CONVERT_TZ(history_date, 'PST8PDT', 'UTC') WHERE history_date >= '1969-12-31 16:00:01';
UPDATE review_historicalreviewrequest SET history_date = CONVERT_TZ(history_date, 'PST8PDT', 'UTC') WHERE history_date >= '1969-12-31 16:00:01';
UPDATE review_historicalreviewrequest SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE review_historicalunavailableperiod SET history_date = CONVERT_TZ(history_date, 'PST8PDT', 'UTC') WHERE history_date >= '1969-12-31 16:00:01';
UPDATE review_reviewassignment SET assigned_on = CONVERT_TZ(assigned_on, 'PST8PDT', 'UTC') WHERE assigned_on >= '1969-12-31 16:00:01';
UPDATE review_reviewassignment SET completed_on = CONVERT_TZ(completed_on, 'PST8PDT', 'UTC') WHERE completed_on >= '1969-12-31 16:00:01';
UPDATE review_reviewrequest SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE review_reviewwish SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE south_migrationhistory SET applied = CONVERT_TZ(applied, 'PST8PDT', 'UTC') WHERE applied >= '1969-12-31 16:00:01';
UPDATE submit_preapproval SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE submit_submissioncheck SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE submit_submissionevent SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';
UPDATE tastypie_apikey SET created = CONVERT_TZ(created, 'PST8PDT', 'UTC') WHERE created >= '1969-12-31 16:00:01';
UPDATE utils_versioninfo SET time = CONVERT_TZ(time, 'PST8PDT', 'UTC') WHERE time >= '1969-12-31 16:00:01';

UPDATE meeting_timeslot
  JOIN meeting_meeting
    ON meeting_meeting.id = meeting_id
  SET time = CONVERT_TZ(time, time_zone, 'UTC');
"""),
        migrations.RunPython(convert_pre1970_timestamps),
    ]
