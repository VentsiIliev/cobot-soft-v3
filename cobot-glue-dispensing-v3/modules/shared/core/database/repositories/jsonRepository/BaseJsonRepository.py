import json

from modules.shared.core.database.repositories.BaseRepository import BaseRepository
class BaseJsonRepository(BaseRepository):
    def __init__(self, file_path):
        self.file_path = file_path

    def read(self):
        with open(self.file_path, 'r') as file:
            return json.load(file)

    def write(self, data):
        with open(self.file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def insert(self, data):
        all_data = self.read()
        all_data.append(data)
        self.write(all_data)
        return data

    def get(self, id):
        all_data = self.read()
        for data in all_data:
            if data.get('id') == id:
                return data
        return None

    def update(self, id, data):
        all_data = self.read()
        for i, d in enumerate(all_data):
            if d.get('id') == id:
                all_data[i] = data
                self.write(all_data)
                return data
        return None
