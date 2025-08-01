# Load in census boundaries (municipalities, census tracts, block groups, and blocks)
localdir <- "K:/DataServices/Datasets/MassGIS/Census_2010"
setwd(localdir)

# load Massachusetts geometries
mass.towns <- readOGR(dsn = ".", layer = "CENSUS2010TOWNS_POLY", stringsAsFactors = FALSE, encoding = "latin1")
mass.ct <- readOGR(dsn = ".", layer = "CENSUS2010TRACTS_POLY", stringsAsFactors = FALSE, encoding = "latin1") 
mass.bg <- readOGR(dsn = ".", layer = "CENSUS2010BLOCKGROUPS_POLY", stringsAsFactors = FALSE, encoding = "latin1")
mass.blocks <-  readOGR(dsn = ".", layer = "CENSUS2010BLOCKS_POLY", stringsAsFactors = FALSE, encoding = "latin1")

# transform geometry CRSes to match that of mass.towns (projected, in meters)
mass.towns <- spTransform(mass.towns, CRSobj = CRS("+proj=utm +zone=20 ellps=WGS84"))
mass.ct <- spTransform(mass.ct, CRSobj = proj4string(mass.towns))
mass.bg <- spTransform(mass.bg, CRSobj = proj4string(mass.towns))
mass.blocks <- spTransform(mass.blocks, CRSobj = proj4string(mass.towns))