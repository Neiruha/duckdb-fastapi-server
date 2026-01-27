from __future__ import annotations

from typing import Dict, List

from .connection import dictrows, get_conn


def list_metrics() -> List[Dict[str, object]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT
                metric_id AS id,
                name,
                kind,
                system,
                code,
                members_json AS members,
                definition AS description
            FROM metrics
            ORDER BY name ASC
            """
        )
        return dictrows(cur)


def list_metric_types() -> List[Dict[str, object]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT DISTINCT kind AS id
            FROM metrics
            ORDER BY kind ASC
            """
        )
        return dictrows(cur)


def list_track_step_types() -> List[Dict[str, object]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT step_type AS id, description
            FROM track_step_types
            ORDER BY description ASC
            """
        )
        return dictrows(cur)


def list_sys_event_types() -> List[Dict[str, object]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT event_type AS id, description
            FROM sys_event_types
            ORDER BY description ASC
            """
        )
        return dictrows(cur)


def list_message_types() -> List[Dict[str, object]]:
    with get_conn(True) as con:
        cur = con.execute(
            """
            SELECT message_type AS id, description
            FROM message_types
            ORDER BY description ASC
            """
        )
        return dictrows(cur)
