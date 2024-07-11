import argparse
import os
from datetime import timedelta
from typing import Dict

from prefect import flow, task

from moovitamix_data_connector.moovitamix_api_connector import MoovitamixApiConnector
from moovitamix_data_connector.utils import get_project_root, load_yaml


@task(name="fetch_tracks_datasource", log_prints=True)
def fetch_tracks_datasource(moovitamix_api_connector: MoovitamixApiConnector, datacatalog: Dict) -> None:
    if moovitamix_api_connector.check_connection():
        tracks_df = moovitamix_api_connector.fetch_tracks_from_api()
        moovitamix_api_connector.save_dataframe_to_parquet(df=tracks_df, file_path=os.path.join(get_project_root(), datacatalog['src_tracks']['filepath']))

@task(name="fetch_users_datasource", log_prints=True)
def fetch_users_datasource(moovitamix_api_connector: MoovitamixApiConnector, datacatalog: Dict) -> None:
    if moovitamix_api_connector.check_connection():
        users_df = moovitamix_api_connector.fetch_users_from_api()
        moovitamix_api_connector.save_dataframe_to_parquet(df=users_df, file_path=os.path.join(get_project_root(), datacatalog['src_users']['filepath']))

@task(name="listen_history", log_prints=True)
def fetch_listen_history_datasource(moovitamix_api_connector: MoovitamixApiConnector, datacatalog: Dict) -> None:
    if moovitamix_api_connector.check_connection():
        listen_history_df = moovitamix_api_connector.fetch_listen_history_from_api()
        moovitamix_api_connector.save_dataframe_to_parquet(df=listen_history_df, file_path=os.path.join(get_project_root(), datacatalog['src_listen_history']['filepath']))


@flow(name="moovitamix-api-extraction", log_prints=True)
def main():
    datacatalog = load_yaml(file_path=os.path.join(get_project_root(), "conf/base/catalog.yml"))
    #TODO: In a normal dev/prod context, the api credentials should be moved into a secrets file or a secrets manager
    moovitamix_connector = MoovitamixApiConnector(base_url="http://127.0.0.1:8000", api_key=None)

    # tracks
    fetch_tracks_datasource(moovitamix_connector, datacatalog)
    # users
    fetch_users_datasource(moovitamix_connector, datacatalog)
    # listen history
    fetch_listen_history_datasource(moovitamix_connector, datacatalog)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scheduling option.")
    parser.add_argument('--scheduling', type=str, choices=['yes', 'no'], required=True, help='Enable or disable scheduling (yes or no)')
    args = vars(parser.parse_args())
    if args['scheduling'] == 'yes':
        main.serve(name="music-recommendation-data-pipeline", interval=timedelta(minutes=1))
    elif args['scheduling'] == 'no':
        main()

