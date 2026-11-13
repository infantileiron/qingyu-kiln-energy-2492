from uuid import uuid4
from sqlalchemy import select
from fastapi import HTTPException
from ..models.dataset import MeterDataset
from .readings import parse_csv

def create(db,body):
 if db.scalar(select(MeterDataset).where(MeterDataset.name==body.name)):raise HTTPException(409,"观测批次名称已存在")
 try:readings=parse_csv(body.csv_text,body.mode)
 except ValueError as e:raise HTTPException(422,str(e))
 row=MeterDataset(id=str(uuid4()),name=body.name,description=body.description,readings=readings,source_mode=body.mode);db.add(row);db.commit();return row
