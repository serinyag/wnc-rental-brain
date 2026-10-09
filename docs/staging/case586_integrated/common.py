import json,sys
from pathlib import Path
import psycopg
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.phase_05_search.semantic_common import load_env_value
from tools.phase_08_workflow.outlook_inbound_service import connection_runner
from tools.phase_08_workflow.test_console_service import TestConsoleService,TestConsoleConfig
from tools.runtime_environment import AppRuntimeConfig,AppEnvironment
from tools.staging_calibration.run_operator_calibration import build_client
OUT=Path(__file__).parent

def connect():
 assert load_env_value('SUPABASE_PROJECT_REF')=='mspcopnsbounmdpivkvq'
 return psycopg.connect(host='db.mspcopnsbounmdpivkvq.supabase.co',dbname='postgres',user='postgres',password=load_env_value('SUPABASE_DB_PASSWORD'),sslmode='require',connect_timeout=15)
def service(conn):return TestConsoleService(query_runner=connection_runner(conn),config=TestConsoleConfig(runtime=AppRuntimeConfig(app_env=AppEnvironment.STAGING),allow_real_providers=False))
def client():return build_client(ROOT/'Staging Authentications.txt',timeout_seconds=300)
def save(name,value):
 with (OUT/(name+'.json')).open('x') as f:json.dump(value,f,indent=2,default=str)
