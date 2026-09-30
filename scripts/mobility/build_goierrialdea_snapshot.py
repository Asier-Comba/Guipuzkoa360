"""Construye un snapshot GO01 compacto desde un ZIP GTFS descargado fuera del runtime."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path


def rows(archive: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    if name not in archive.namelist():
        return []
    with archive.open(name) as handle:
        return list(csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig", newline="")))


def integer_fields(item: dict[str, str]) -> dict[str, object]:
    result: dict[str, object] = dict(item)
    for field, default in (("stop_sequence",None), ("pickup_type",0), ("drop_off_type",0), ("timepoint",1)):
        raw = result.get(field)
        if raw in (None, ""):
            if default is None:
                raise ValueError("missing stop_sequence")
            result[field] = default
        else:
            result[field] = int(str(raw))
    return result


def build(source: Path, output: Path, metadata: dict[str, object]) -> dict[str, object]:
    for field in ("snapshot_id", "retrieved_date", "url", "validated_dates"):
        if not metadata.get(field):
            raise ValueError("download metadata required: " + field)
    if output.exists():
        raise ValueError("Refusing to overwrite a historical snapshot; use a new output identity")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if metadata.get('source_sha256') and metadata['source_sha256'] != source_hash:
        raise ValueError('source bytes do not match download metadata')
    with zipfile.ZipFile(source) as archive:
        routes = rows(archive, "routes.txt")
        route = next(item for item in routes if item["route_short_name"].upper() == "GO01")
        trips = [item for item in rows(archive, "trips.txt") if item["route_id"] == route["route_id"]]
        trip_ids = {item["trip_id"] for item in trips}
        times_by_trip: dict[str, list[dict[str, object]]] = {trip_id: [] for trip_id in trip_ids}
        for item in rows(archive, "stop_times.txt"):
            if item["trip_id"] in trip_ids:
                normalized = integer_fields(item)
                times_by_trip[item["trip_id"]].append({
                    "stop_id": normalized["stop_id"],
                    "sequence": normalized["stop_sequence"],
                    "arrival": normalized["arrival_time"],
                    "departure": normalized["departure_time"],
                    "pickup_type": normalized["pickup_type"],
                    "drop_off_type": normalized["drop_off_type"],
                    "timepoint": normalized["timepoint"],
                })
        calendars = rows(archive, "calendar.txt")
        for row in calendars:
            for field in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"):
                row[field] = int(row[field])
        calendar_dates = rows(archive, "calendar_dates.txt")
        for row in calendar_dates:
            row["exception_type"] = int(row["exception_type"])
        feed_info = rows(archive, "feed_info.txt")[0]
        stop_ids = {row['stop_id'] for items in times_by_trip.values() for row in items}
        stops = {row['stop_id']: {'name':row['stop_name'], 'lat':float(row['stop_lat']), 'lon':float(row['stop_lon'])}
                 for row in rows(archive, 'stops.txt') if row['stop_id'] in stop_ids}
    payload: dict[str, object] = {
        "schema_version": "0.2.0",
        "snapshot_id": metadata['snapshot_id'],
        "scenario_kind": "stop_only",
        "fixture_kind": "OFFICIAL_DERIVED",
        "timezone": "Europe/Madrid",
        "coverage": {"start_date": feed_info["feed_start_date"], "end_date": feed_info["feed_end_date"], "validated_dates": metadata['validated_dates'], "direct_search_complete":True},
        "stops":stops,
        "defaults": {"arrival_margin_minutes": 10, "boarding_margin_minutes": 3, "walking_profile_id": "stop_only"},
        "walking_profiles": {"stop_only": {"description": "Análisis entre pares de paradas; no infiere velocidad peatonal", "source": "GTFS stops"}},
        "origins": {
            "zegama_center_stops": {"name": "Paradas centrales de Zegama", "stop_ids": ["8305", "8309"], "access_s_by_stop": {"8305": 0, "8309": 0}},
            "segura_herriko_plaza_stops": {"name": "Paradas Herriko Plaza de Segura", "stop_ids": ["7801", "7813"], "access_s_by_stop": {"7801": 0, "7813": 0}},
            "idiazabal_center_stops": {"name": "Paradas centrales de Idiazabal", "stop_ids": ["7903", "7906"], "access_s_by_stop": {"7903": 0, "7906": 0}}
        },
        "destinations": {
            "beasain_center_stop_pair": {"name": "Par de paradas del centro de Beasain", "stop_ids": ["7214", "7218"], "walk_s_by_stop": {"7214": 0, "7218": 0}}
        },
        "calendar": calendars,
        "calendar_dates": calendar_dates,
        "trips": [{"trip_id": trip["trip_id"], "service_id": trip["service_id"], "route_id": trip["route_id"], "direction_id": trip.get("direction_id", ""), "stops": sorted(times_by_trip[trip["trip_id"]], key=lambda row: int(row["sequence"]))} for trip in trips],
        "sources": [{
            "classification": "OFFICIAL",
            "publisher": "Gobierno Vasco / Moveuskadi",
            "operator_feed": "Lurraldebus Goierrialdea",
            "url": metadata['url'],
            "source_id": "MOVEUSKADI_GOIERRIALDEA_" + source_hash[:12],
            "index_url": "https://opendata.euskadi.eus/transport/moveuskadi/data-index-gtfs.json",
            "index_last_update": metadata.get('index_last_update'),
            "source_sha256": source_hash,
            "feed_version": feed_info.get("feed_version"),
            "retrieved_date": metadata['retrieved_date']
        }],
        "limitations": [
            "Solo GO01 y viajes directos entre los pares de paradas catalogados.",
            "Los tiempos tienen timepoint=0; son tiempos aproximados/interpolados del feed.",
            "No demuestra un desplazamiento real, puntualidad, accesibilidad universal ni cobertura desde viviendas.",
            "La ausencia de calendar_dates no se interpreta por sí sola como corrupción del GTFS.",
            "Destino piloto en paradas del centro de Beasain; no reproduce el paseo al ambulatorio de la PoC histórica."
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_zip", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    args = parser.parse_args()
    payload = build(args.source_zip, args.output_json, json.loads(args.metadata.read_text(encoding='utf-8')))
    print(json.dumps({"snapshot_id": payload["snapshot_id"], "trips": len(payload["trips"]), "output": str(args.output_json)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
