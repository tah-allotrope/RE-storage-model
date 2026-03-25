"""Firebase Cloud Function entrypoints for RE-Storage web APIs."""

from __future__ import annotations

import functions_framework
from flask import Request
from flask_cors import cross_origin
from handlers.compare_scenarios import handle_compare_scenarios
from handlers.run_excel import handle_run_excel
from handlers.run_json import handle_run_json
from handlers.run_sensitivity import handle_run_sensitivity


@functions_framework.http
@cross_origin()
def runExcel(request: Request):  # noqa: N802
    return handle_run_excel(request)


@functions_framework.http
@cross_origin()
def runJson(request: Request):  # noqa: N802
    return handle_run_json(request)


@functions_framework.http
@cross_origin()
def compareScenarios(request: Request):  # noqa: N802
    return handle_compare_scenarios(request)


@functions_framework.http
@cross_origin()
def runSensitivity(request: Request):  # noqa: N802
    return handle_run_sensitivity(request)
