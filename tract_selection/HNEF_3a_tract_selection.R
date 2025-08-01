# install pacman package, which helps simplify installation and loading of packages
# remotes::install_github("cran/GISTools")
# install.packages("pacman", repos = "http://cran.us.r-project.org")


# load required packages
pacman::p_load(sp, rgdal, rgeos, GISTools, maptools, plyr, dplyr, tidyverse, reshape2, ggmap, RPostgreSQL, classInt)


######## OPEN ADDRESS FILE AND GEOCODE ADDRESSES ########

# Read addresses from local file
file.to.load = "/Users/chris/DeepGreen/workspaces/tamarack/clf-healthscore/tract_selection/HNEF_address.csv" # <- file.choose(new=TRUE)

# read the csv files into a variable (and do not read strings as factors)
addresses <- read.csv(file.to.load, stringsAsFactors = FALSE)

# initialize a data frame for geocoding (the data frame will remain empty even after geocoding, so don't worry)
geocoded <- data.frame(stringsAsFactors = FALSE)

register_google(key = 'AIzaSyC4eMcin-9n2Ly3nNKnvL3_xfGogpntEZE', )

# for loop to read addresses from csv file and geocode them using Google Maps API
for (i in 1:nrow(addresses)) {
  result <- geocode(location = addresses$address[i], output = "latlon", source = "google")
  addresses$lon[i] <- as.numeric(result[1])
  addresses$lat[i] <- as.numeric(result[2])
}


# write to a new csv file
write.csv(addresses, "HNEF_geocoded.csv", row.names=FALSE)

######## MAP GEOCODED ADDRESS(ES) AND CREATE 0.5 MILE BUFFER ########

addresses = read.csv("HNEF_geocoded.csv", stringsAsFactors = FALSE)

# transform address lat/long to universal transverse mercator (UTM) to allow for distance buffers
latlong <- data.frame(cbind(addresses$lat, addresses$lon))
names(latlong) <- c("X", "Y")
coordinates(latlong) <- ~ Y + X # longitude first
proj4string(latlong) <- CRS("+proj=longlat + ellps=WGS84 +datum=WGS84")
utm <- spTransform(latlong, CRS("+proj=utm +zone=20 ellps=WGS84"))

# establish the 0.5 mile buffer (805 meters = 0.5 miles)
utm.buffer <- gBuffer(spgeom=utm, byid=TRUE, width=805)

# load Massachusetts geometries
mass.towns <- readOGR(dsn = "/DeepGreen/Tamarack/CLF/MassGIS", layer = "CENSUS2020TOWNS_POLY", stringsAsFactors = FALSE, encoding = "latin1")
mass.ct <- readOGR(dsn = "/DeepGreen/Tamarack/CLF/MassGIS", layer = "CENSUS2020TRACTS_POLY", stringsAsFactors = FALSE, encoding = "latin1")
mass.bg <- readOGR(dsn = "/DeepGreen/Tamarack/CLF/MassGIS", layer = "CENSUS2020BLOCKGROUPS_POLY", stringsAsFactors = FALSE, encoding = "latin1")
mass.blocks <-  readOGR(dsn = "/DeepGreen/Tamarack/CLF/MassGIS", layer = "CENSUS2020BLOCKS_POLY", stringsAsFactors = FALSE, encoding = "latin1")

# transform geometry CRSes to match that of mass.towns (projected, in meters)
mass.towns <- spTransform(mass.towns, CRSobj = CRS("+proj=utm +zone=20 ellps=WGS84"))
mass.ct <- spTransform(mass.ct, CRSobj = proj4string(mass.towns))
mass.bg <- spTransform(mass.bg, CRSobj = proj4string(mass.towns))
mass.blocks <- spTransform(mass.blocks, CRSobj = proj4string(mass.towns))

# determine the blocks that are covered by the 0.5 mile buffer
mass.blocks.centroid <- gCentroid(mass.blocks, byid = TRUE)
overlap.blk <- mass.blocks[!is.na(over(mass.blocks.centroid,utm.buffer)),]

# head(mass.blocks)

######## DETERMINING CENSUS TRACTS TO SELECT ########
# change population variables to numeric (original data type: character)
mass.blocks@data$POP20 <- as.numeric(mass.blocks@data$POP20)
mass.ct@data$POP20 <- as.numeric(mass.ct@data$POP20)

overlap.ct <- mass.ct[!is.na(over(mass.ct,utm.buffer)),]

class(overlap.ct)

overlap.ct <- overlap.ct[overlap.ct@data$TRACTCE20 %in% unique(overlap.blk@data$TRACTCE20),]

# determine the blocks in tract that are within the buffer zone and sum the population by tract
blks.in.tract <- c()

for (i in 1:length(unique(overlap.blk$TRACTCE20))) {
  blks.in.tract[i] <- sum(overlap.blk@data[overlap.blk@data$TRACTCE20==overlap.ct$TRACTCE20[i],]$POP20)
}

t <- mass.ct[mass.ct$GEOID20 %in% overlap.ct$GEOID20,]


# determine block group of development
overlap.bg <- mass.bg[!is.na(over(mass.bg,utm)),]

# study area 1 = 50%+ of population within 0.5 mile radius
sum.df.1 <- data.frame(overlap.ct$GEOID20, blks.in.tract, t$POP20, blks.in.tract >= 0.5*t$POP20)
colnames(sum.df.1) <- c("tract", "pop.blks.in.tract", "totpop", "majority.in.buffer")
sa1 <- sum.df.1$tract[sum.df.1$majority.in.buffer == TRUE]
sa1 <- as.numeric(as.character(sa1))
sa1_name <- paste(addresses$study.area, 1, sep = " ") 
sa1_bg <- overlap.bg@data$GEOID20
sa1_muni <- addresses$municipality

sa1

sa1_name

sa1_bg

sa1_muni

# study area 2 = 40%+ of population within 0.5 mile radius
# sum.df.2 <- data.frame(overlap.ct$GEOID20, blks.in.tract, t$POP20, blks.in.tract > 0.4*t$POP20)
# colnames(sum.df.2) <- c("tract", "pop.blks.in.tract", "totpop", "majority.in.buffer")
# sa2 <- sum.df.2$tract[sum.df.2$majority.in.buffer == TRUE]
# sa2 <- as.numeric(as.character(sa2))
# sa2_name <- paste(addresses$study.area, 2, sep = " ")
# sa2_bg <- overlap.bg@data$GEOID20
# sa2_muni <- addresses$municipality

######## MAPPING ########
# Create a natural jenks shading scheme
# jenks <- classIntervals(mass.blocks@data$POP20[mass.blocks$REALTOWN == addresses$municipality], n=5, style="jenks")
# shades <- shading(jenks$brks, cols = brewer.pal(5, "Greys"))
#
# localdir <- "K:/DataServices/Projects/Current_Projects/Healthy_Neighborhoods_Equity_Funds"
# setwd(localdir)
#
# # plot study area 1
# pdf(paste0("sa1_", tolower(gsub(" ", "", addresses$study.area, fixed = TRUE)), ".pdf"), width = 8.5, height = 11)
#
# plot(mass.ct[mass.ct$GEOID10 %in% sum.df.1$tract[sum.df.1$majority.in.buffer == TRUE],],
#      border = NA)
#
# plot(mass.blocks[mass.blocks$GEOID10 %in% overlap.blk$GEOID10,],
#      border = "grey47",
#      add=TRUE)
#
# choropleth(mass.blocks[mass.blocks$REALTOWN == addresses$municipality,],
#            mass.blocks@data$POP20[mass.blocks$REALTOWN == addresses$municipality],
#            shading = shades,
#            border = "grey47",
#            add=TRUE)
#
# plot(utm,
#      pch=16,
#      cex = 2.5,
#      col = "magenta",
#      add=TRUE)
#
# plot(utm.buffer,
#      border = "magenta",
#      lwd = 3,
#      add=TRUE)
#
# plot(mass.ct[mass.ct$GEOID10 %in% sum.df.1$tract[sum.df.1$majority.in.buffer == TRUE],],
#      border = "darkgoldenrod2",
#      lwd = 3,
#      add=TRUE)
#
# plot(mass.towns[mass.towns$TOWN==addresses$municipality,],
#      border = "black",
#      add = TRUE)
#
# dev.off()
#
# # plot study area 2
# pdf(paste0("sa2_", tolower(gsub(" ", "", addresses$study.area, fixed = TRUE)), ".pdf"), width = 8.5, height = 11)
#
# plot(mass.ct[mass.ct$GEOID10 %in% sum.df.2$tract[sum.df.2$majority.in.buffer == TRUE],],
#      border = NA)
#
# plot(mass.blocks[mass.blocks$GEOID10 %in% overlap.blk$GEOID10,],
#      border = "grey47",
#      add=TRUE)
#
# choropleth(mass.blocks[mass.blocks$REALTOWN == addresses$municipality,],
#            mass.blocks@data$POP20[mass.blocks$REALTOWN == addresses$municipality],
#            shading = shades,
#            border = "grey47",
#            add=TRUE)
#
# plot(utm,
#      pch=16,
#      cex = 2.5,
#      col = "magenta",
#      add=TRUE)
#
# plot(utm.buffer,
#      border = "magenta",
#      lwd = 3,
#      add=TRUE)
#
# plot(mass.ct[mass.ct$GEOID10 %in% sum.df.2$tract[sum.df.2$majority.in.buffer == TRUE],],
#      border = "darkgoldenrod2",
#      lwd = 3,
#      add=TRUE)
#
# plot(mass.towns[mass.towns$TOWN==addresses$municipality,],
#      border = "black",
#      add = TRUE)
#
# dev.off()
