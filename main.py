from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# Database setup (assuming PostgreSQL)
DATABASE_URL = "postgresql://user:password@db:5432/mes_db" # Use 'db' as hostname for docker-compose/k8s service name

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# SQLAlchemy Models
class Item(Base):
    __tablename__ = "items"
    item_code = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String) # 원자재, 반제품, 완제품
    unit = Column(String)

class ProductionPlan(Base):
    __tablename__ = "production_plans"
    plan_id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String, index=True)
    quantity = Column(Integer)
    status = Column(String, default="pending") # pending, in_progress, completed

class Equipment(Base):
    __tablename__ = "equipments"
    equipment_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    status = Column(String, default="IDLE") # RUN, IDLE

class BOM(Base):
    __tablename__ = "bom"
    product_item_code = Column(String, ForeignKey("items.item_code"), primary_key=True)
    component_item_code = Column(String, ForeignKey("items.item_code"), primary_key=True)
    quantity = Column(Integer)

# Pydantic Models for request/response
class ItemCreate(BaseModel):
    item_code: str
    name: str
    type: str
    unit: str

class ItemResponse(ItemCreate):
    pass

class ProductionPlanCreate(BaseModel):
    item_code: str
    quantity: int

class ProductionPlanResponse(ProductionPlanCreate):
    plan_id: int
    status: str

class EquipmentUpdate(BaseModel):
    status: str

class EquipmentResponse(BaseModel):
    equipment_id: str
    name: str
    status: str

class BOMCreate(BaseModel):
    product_item_code: str
    component_item_code: str
    quantity: int

class BOMResponse(BOMCreate):
    pass

# FastAPI app initialization
app = FastAPI()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine) # Create tables on startup

@app.get("/")
def read_root():
    return {"message": "Welcome to the MES API"}

# REQ-004: 품목 관리 (Item Management)
@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/", response_model=list[ItemResponse])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(Item).offset(skip).limit(limit).all()
    return items

# REQ-010: 생산 계획 (Production Plans)
@app.post("/production_plans/", response_model=ProductionPlanResponse)
def create_production_plan(plan: ProductionPlanCreate, db: Session = Depends(get_db)):
    db_plan = ProductionPlan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@app.get("/production_plans/", response_model=list[ProductionPlanResponse])
def read_production_plans(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    plans = db.query(ProductionPlan).offset(skip).limit(limit).all()
    return plans

# REQ-010: 설비 모니터링 (Equipment Monitoring)
@app.get("/equipments/", response_model=list[EquipmentResponse])
def read_equipments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    equipments = db.query(Equipment).offset(skip).limit(limit).all()
    return equipments

@app.put("/equipments/{equipment_id}", response_model=EquipmentResponse)
def update_equipment_status(equipment_id: str, equipment: EquipmentUpdate, db: Session = Depends(get_db)):
    db_equipment = db.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    db_equipment.status = equipment.status
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

# BOM Management
@app.post("/bom/", response_model=BOMResponse)
def create_bom_entry(bom: BOMCreate, db: Session = Depends(get_db)):
    db_bom = BOM(**bom.dict())
    db.add(db_bom)
    db.commit()
    db.refresh(db_bom)
    return db_bom

@app.get("/bom/{product_item_code}", response_model=list[BOMResponse])
def get_bom_for_product(product_item_code: str, db: Session = Depends(get_db)):
    bom_entries = db.query(BOM).filter(BOM.product_item_code == product_item_code).all()
    if not bom_entries:
        raise HTTPException(status_code=404, detail="BOM for product not found")
    return bom_entries
