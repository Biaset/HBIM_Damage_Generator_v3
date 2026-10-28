import ifcopenshell.api as api
from ifcopenshell.guid import new as new_guid
from datetime import datetime
from sklearn.cluster import DBSCAN
import hashlib
import ifcopenshell.guid as guid
import pandas as pd


def pset_epoch_id(date_str):
    dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    epoch_id = dt.strftime('%d%m%Y')
    pset = f'PTUM_BiologicalColonization_{epoch_id}'
    return pset


class IfcQuery:
    def __init__(self, guid, model):
        self.guid = guid
        self.model = model

    def find_element_by_guid(self):
        return self.model.by_guid(self.guid)

    def guid_to_ifc_type(self):
        if pd.isna(self.guid):
            return None
        elem = self.model.by_guid(str(self.guid))
        return elem.is_a() if elem else None


class ElementDamageClustering:
    def __init__(self, df):
        self.df = df

    def clustering_space(self, host_ifc_class):
        if host_ifc_class == 'IfcWall':
            return '2D'
        else:
            return '3D'

    def cluster_2d(self, eps=0.03, min_samples=20):
        points = self.df[['X', 'Y']].to_numpy()
        labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(points)
        self.df['cluster_id'] = labels
        return self.df

    def cluster_3d(self, eps=0.02, min_samples=10):
        points = self.df[['X', 'Y', 'Z']].to_numpy()
        labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(points)
        self.df['cluster_id'] = labels
        return self.df

    def cluster_properties(self):
        clusters = []
        for cid, group in self.df.groupby('cluster_id'):
            if cid == -1:
                continue
            clusters.append({
                'cluster_id': cid,
                'centroid': group[['X', 'Y', 'Z']].mean().to_numpy(),
                'point_count': len(group),
                #'severity': group['Intensity'].mean(),
                'damage_type': group['damage_type'].iloc[0],
                'host_id': group['host_id'].iloc[0],
                'ifc_type': group['ifc_type'].iloc[0],
                'timestamp': group['Timestamp'].iloc[0]
            })
        return clusters


# def stable_damage_guid(host_id, damage_type, centroid):
#     key = f'{host_id}_{damage_type}_{round(centroid[0], 2)}_{round(centroid[1], 2)}_{round(centroid[2], 2)}'
#     h = hashlib.sha1(key.encode()).hexdigest()[:22]
#     return guid.compress(h)

def stable_damage_guid(host_id, damage_type, centroid):
    key = f"{host_id}_{damage_type}_{round(centroid[0], 2)}_{round(centroid[1], 2)}_{round(centroid[2], 2)}"

    # full 32 hex chars (128 bits)
    h = hashlib.md5(key.encode()).hexdigest()  # <-- use md5 (32 hex chars)

    return guid.compress(h)


class DamageCreation:
    def __init__(self, model):
        #self.element = element
        self.model = model
        #self.pset_name = pset_name
        # self.covering = None
        # self.proxy = None
        #self.storey = self.element.ContainedInStructure[0].RelatingStructure
        self.storey = None
        self.product = None
        self.new_guid = None

    def get_or_create_damage(self, guid_value, element, damage_name, damage_type):
        for obj in self.model.by_type('IfcProduct'):
            if obj.GlobalId == guid_value:
                return obj

        if damage_type in ['Lichen', 'Moss', 'Bacteria']:

            self.product = api.run(
                'root.create_entity',
                self.model,
                ifc_class='IfcSurfaceFeature',
                name=damage_name
            )

            self.new_guid = self.product.GlobalId

            # self.product = self.model.create_entity(
            #     "IfcCovering",
            #     GlobalId=guid_value,
            #     # OwnerHistory=model.by_type("IfcOwnerHistory")[0],
            #     Name=damage_name,
            #     PredefinedType="USERDEFINED"
            # )

            self.product.PredefinedType = 'DEFECT'
            storey = element.ContainedInStructure[0].RelatingStructure

            rel = api.run(
                'root.create_entity',
                self.model,
                ifc_class="IfcRelAdheresToElement"
            )
            rel.RelatingElement = element
            rel.RelatedSurfaceFeatures = [self.product]

            api.run(
                'spatial.assign_container',
                self.model,
                products=[self.product],
                relating_structure=storey
            )

        else:
            self.product = api.run(
                'root.create_entity',
                self.model,
                ifc_class='IfcSurfaceFeature',
                name=damage_name
            )

            self.new_guid = self.product.GlobalId
            self.product.PredefinedType = 'DEFECT'
            storey = element.ContainedInStructure[0].RelatingStructure

            rel = api.run(
                'root.create_entity',
                self.model,
                ifc_class="IfcRelAdheresToElement"
            )
            rel.RelatingElement = element
            rel.RelatedSurfaceFeatures = [self.product]

            api.run(
                'spatial.assign_container',
                self.model,
                products=[self.product],
                relating_structure=storey
            )
        return self.product, self.new_guid


    # def create_new_covering_damage(self, element, damage_name):
    #     self.covering = api.run(
    #         'root.create_entity',
    #         self.model,
    #         ifc_class='IfcCovering',
    #         name=damage_name
    #     )
    #
    #     self.covering.PredefinedType = 'USERDEFINED'
    #     storey = element.ContainedInStructure[0].RelatingStructure
    #
    #     rel = api.run(
    #         'root.create_entity',
    #         self.model,
    #         ifc_class="IfcRelCoversBldgElements"
    #     )
    #     rel.RelatingBuildingElement = element
    #     rel.RelatedCoverings = [self.covering]
    #
    #     api.run(
    #         'spatial.assign_container',
    #         self.model,
    #         products=[self.covering],
    #         relating_structure=storey
    #     )

        # owner_history = self.model.by_type("IfcOwnerHistory")[0]
        #
        # rel = self.model.create_entity(
        #     "IfcRelCoversBldgElements",
        #     GlobalId=new_guid(),
        #     OwnerHistory=owner_history,
        #     RelatingBuildingElement=self.element,
        #     RelatedCoverings=[self.covering],
        # )

        # api.run(
        #     "aggregate.assign_object",
        #     self.model,
        #     products=[self.covering],
        #     relating_object=self.element
        # )

    # def pset_for_covering_damage(self, properties, pset_name):
    #     pset = api.run(
    #         'pset.add_pset',
    #         self.model,
    #         product=self.covering,
    #         name=pset_name
    #     )
    #
    #     api.run(
    #         'pset.edit_pset',
    #         self.model,
    #         pset=pset,
    #         properties=properties
    #     )

    # def create_new_proxy_damage(self, element, damage_name):
    #     self.proxy = api.run(
    #             'root.create_entity',
    #             self.model,
    #             ifc_class='IfcBuildingElementProxy',
    #             name=damage_name
    #         )
    #
    #     self.proxy.PredefinedType = 'USERDEFINED'
    #     storey = element.ContainedInStructure[0].RelatingStructure
    #
    #     rel = api.run(
    #         'root.create_entity',
    #         self.model,
    #         ifc_class="IfcRelAssignsToProduct"
    #     )
    #     rel.RelatingProduct = element
    #     rel.RelatedObjects = [self.proxy]
    #
    #     api.run(
    #         'spatial.assign_container',
    #         self.model,
    #         products=[self.proxy],
    #         relating_structure=storey
    #     )

    # def psets_for_proxy_damage(self, properties, pset_name):
    #     pset = api.run(
    #         'pset.add_pset',
    #         self.model,
    #         product=self.proxy,
    #         name=pset_name
    #     )
    #
    #     api.run(
    #         'pset.edit_pset',
    #         self.model,
    #         pset=pset,
    #         properties=properties
    #     )

    def attach_epoch_pset(self, properties, pset_name):

        pset = api.run(
            'pset.add_pset',
            self.model,
            product=self.product,
            name=pset_name
        )

        api.run(
            'pset.edit_pset',
            self.model,
            pset=pset,
            properties=properties
        )
        return pset


    def ingest_multiple_damage_dict(self, element, dict_of_pset_damage, pset_name):
        for name, prop in dict_of_pset_damage.items():
            if name == 'BiologicalColonization_Plant':
                self.create_new_proxy_damage(element, name)
                self.psets_for_proxy_damage(prop, pset_name)
            else:
                self.create_new_covering_damage(element, name)
                self.pset_for_covering_damage(prop, pset_name)

    def ingest_multiple_damage_csv(self, csv, pset_name, observation_time):
        for _, row in csv.iterrows():
            if row['timestamp'] == observation_time:
                element = IfcQuery(row['host_id'], self.model).find_element_by_guid()
                cluster_id = row['cluster_id']
                damage = row['damage_type']
                damage_guid = row['damage_id']
                damage_name = f'PTUM_BiologicalColonization'
                if row["point_count"] < 500:
                    severity = "LOW"
                elif row["point_count"] < 5000:
                    severity = "MEDIUM"
                else:
                    severity = "HIGH"
                # prop = {
                #     'DecayType': damage,
                #     # 'CoverageRatio': row['Coverage'],
                #     # 'SeverityLevel': row['Severity'],
                #     'ObservationDate': row['timestamp']
                # }
                prop = {
                    'DecayType': damage,
                    'ObservationTime': row['timestamp'],
                    'SurveyMethod': 'Laser Scanner',
                    'DeviceModel': 'Leica BLK360',
                    'MoistureCorrelation': False,
                    #'SeverityLevel_PTUM': severity,
                    'CoverageArea': '0.23 m2',
                    'WeatherCondition': 'CLOUDY'
                }
                # if damage == 'plant':
                #     self.create_new_proxy_damage(element, damage_name)
                #     self.psets_for_proxy_damage(prop, pset_name)
                # else:
                #     self.create_new_covering_damage(element, damage_name)
                #     self.pset_for_covering_damage(prop, pset_name)

                self.get_or_create_damage(damage_guid, element, damage_name, damage)
                self.attach_epoch_pset(prop, pset_name)

                csv.loc[csv["cluster_id"] == cluster_id, "damage_id"] = self.new_guid

        return csv

    def ingest_single_damage(self, element, damage_type, pset_name, observation_time, element_guid, centroid):
        damage_name = f'BiologicalColonization_{str(damage_type).title()}'
        prop = {
            'DecayType_PTUM': damage_type,
            'ObservationDate_PTUM': observation_time,
            'SurveyMethod_PTUM': 'Laser Scanner',
            'DeviceModel_PTUM': 'Leica BLK360',
            'SurfaceLocation_PTUM': 'External',
            'SeverityLevel_PTUM': 'MEDIUM',
            'CoverageArea_PTUM': '0.23 m2'
        }
        damage_guid = stable_damage_guid(element_guid, damage_type, centroid)
        damage = self.get_or_create_damage(damage_guid, element, damage_name, damage_type)
        self.attach_epoch_pset(prop, pset_name)
        return damage