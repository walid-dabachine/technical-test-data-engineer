import enum
import time
from typing import Any, Dict, List, Union

import pandas as pd
import requests
from pydantic import BaseModel

from moovitamix_data_connector.data_models import ListenHistory, Track, User
from moovitamix_data_connector.utils import validate_datasource


#TODO: Ideally this should be a config to make the ingestion more customizable
class Endpoint(enum.Enum):
    """ Set of finite endpoints to restric users behaviours when calling the API """

    TRACKS = 'tracks'
    USERS = 'users'
    LISTEN_HISTORY = 'listen_history'

class MoovitamixApiConnector:
    PAGE_SIZE = 100

    def __init__(self, base_url: str, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {'Authorization': f'Bearer {self.api_key}'}

    def check_connection(self) -> bool:
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            print("Connection to Moovitamix successful!")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Connection to Moovitamix API failed, here is the reason:\n {e}")
            return False

    def _make_request(self, url: str, **kwargs) -> Union[Dict[str, Any], None]:
        try:
            response = requests.get(url, headers=self.headers, params=kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            RATE_LIMIT_ERROR_CODE = 429
            if response.status_code == RATE_LIMIT_ERROR_CODE:
                # This is a simple mechanism, a backoff strategy would be more suitable moving forward
                retry_after = 5
                print(f"Rate limit reached. Retrying after {retry_after} seconds.")
                time.sleep(retry_after)
                return self._make_request(url=url, kwargs=kwargs)
            else:
                print(f"HTTP error occurred: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")
        return None

    def fetch_tracks_from_api(self) -> pd.DataFrame:
        return self._fetch_endpoint_from_api(endpoint=Endpoint.TRACKS, endpoint_model_class=Track)

    def fetch_users_from_api(self) -> pd.DataFrame:
        return self._fetch_endpoint_from_api(endpoint=Endpoint.USERS, endpoint_model_class=User)

    def fetch_listen_history_from_api(self) -> pd.DataFrame:
        return self._fetch_endpoint_from_api(endpoint=Endpoint.LISTEN_HISTORY, endpoint_model_class=ListenHistory)

    def _fetch_endpoint_from_api(self, endpoint: Endpoint, endpoint_model_class: BaseModel) -> pd.DataFrame:
        json_records = self._fetch_data_from_api(endpoint=endpoint)
        validated_records = validate_datasource(json_records=json_records, cls=endpoint_model_class)
        df_records = pd.DataFrame([record.model_dump() for record in validated_records])
        return df_records

    def save_dataframe_to_parquet(self, df: pd.DataFrame, file_path: str) -> None:
        """
        Save a pandas DataFrame to a Parquet file.
        Args:
            df (pd.DataFrame): pandas DataFrame to save
            file_path (str): Path where the Parquet file will be saved
        """
        try:
            df.to_parquet(file_path, index=False)
            print(f"DataFrame saved to {file_path}")
        except Exception as e:
            print(f"An error occurred while saving the DataFrame to Parquet: {e}")

    def _fetch_data_from_api(self, endpoint: Endpoint) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint.value}"
        data = []
        response_json = self._make_request(url, size=self.PAGE_SIZE, page=1)
        if response_json is None:
            return data
        nb_pages = response_json['pages']
        data.extend(response_json['items'])
        for page_number in range(2, nb_pages + 1):
            response_json = self._make_request(url, size=self.PAGE_SIZE, page=page_number)
            data.extend(response_json['items'])
        print(f"Then endpoint contains a total of {nb_pages} pages, and the connector fetched {len(data)} records")
        return data
