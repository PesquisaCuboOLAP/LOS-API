import enum

class Cluster(str, enum.Enum):
    CODING = "CODING"
    DESIGN = "DESIGN"
    MARKETING = "MARKETING"
    MANAGEMENT = "MANAGEMENT"
    CORE = "CORE"