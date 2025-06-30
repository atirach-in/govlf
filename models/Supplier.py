# models.py
from sqlalchemy import Column, Integer, String, Date, Float
from db import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    GENERICNAME = Column(String, nullable=True)
    HOSPDRUGCODE = Column(String, nullable=True)
    PRODUCTCAT = Column(Integer, nullable=True)
    TMTID = Column(Integer, nullable=True)
    SPECPREP = Column(String, nullable=True)
    TRADENAME = Column(String, nullable=True)
    DFSCODE = Column(String, nullable=True)
    DOSAGEFORM = Column(String, nullable=True)
    STRENGTH = Column(String, nullable=True)
    CONTENT = Column(String, nullable=True)
    UNITPRICE = Column(Float, nullable=True)
    DISTRIBUTOR = Column(String, nullable=True)
    MANUFACTURER = Column(String, nullable=True)
    ISED = Column(String, nullable=True)
    NDC24 = Column(String, nullable=True)
    PACKSIZE = Column(String, nullable=True)
    PACKPRICE = Column(String, nullable=True)
    UPDATEFLAG = Column(String, nullable=True)
    DATECHANGE = Column(Date, nullable=True)
    DATEUPDATE = Column(Date, nullable=True)
    DATEEFFECTIVE = Column(Date, nullable=True)
    ISED_APPROVED = Column(String, nullable=True)
    NDC24_APPROVED = Column(String, nullable=True)
    DATE_APPROVED = Column(Date, nullable=True)
    ISED_STATUS = Column(Integer, nullable=True)
