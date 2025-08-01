# install pacman package, which helps simplify installation and loading of packages
#remotes::install_github("cran/GISTools")
# remotes::install_github("walkerke/tidycensus")
#install.packages("pacman", repos = "http://cran.us.r-project.org")

options(tigris_use_cache = TRUE)

# load required packages
pacman::p_load(sf, rgdal, rgeos, GISTools, maptools, plyr, dplyr, tidyverse, reshape2, ggmap, RPostgreSQL, classInt, tidycensus, tigris)


######## OPEN ADDRESS FILE AND GEOCODE ADDRESSES ########

# open a dialog box that allows you to choose a file with addresses
file.to.load = "/DeepGreen/workspaces/tamarack/clf-healthscore/tract_selection/HNEF_address.csv" # <- file.choose(new=TRUE)

# read the csv files into a variable (and do not read strings as factors)
addresses <- read.csv(file.to.load, stringsAsFactors = FALSE)

# initialize a data frame for geocoding (the data frame will remain empty even after geocoding, so don't worry)
geocoded <- data.frame(stringsAsFactors = FALSE)

# register_google(key = 'AIzaSyAyfnxKnSkY-gh5aPhriZ429BRtdA0evXc', )
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
utm <- st_transform(st_as_sf(latlong), CRS("+proj=utm +zone=20 ellps=WGS84"))

# establish the 0.5 mile buffer (805 meters = 0.5 miles)
utm.buffer <- st_buffer(utm, byid=TRUE, dist=805)

# load Massachusetts geometries
mass.towns <-
  get_decennial(
    year = 2020,
    state = "MA",
    variables = c("P1_001N"),
    geography = "county subdivision",
    geometry = TRUE
)

mass.ct <-
  get_decennial(
    year = 2020,
    state = "MA",
    variables = c("P1_001N"),
    geography = "tract",
    geometry = TRUE
)

mass.ct

mass.bg <-
  get_decennial(
    year = 2020,
    state = "MA",
    variables = c("P1_001N"),
    geography = "block group",
    geometry = TRUE
)
mass.blocks <-
  get_decennial(
    year = 2020,
    state = "MA",
    variables = c("P1_001N"),
    geography = "block",
    geometry = TRUE
)

# transform geometry CRSes to match that of mass.towns (projected, in meters)
mass.towns <-st_transform(mass.towns, CRS("+proj=utm +zone=20 ellps=WGS84"))
mass.ct <- st_transform(mass.ct, CRS("+proj=utm +zone=20 ellps=WGS84"))
mass.bg <- st_transform(mass.bg, CRS("+proj=utm +zone=20 ellps=WGS84"))
mass.blocks <- st_transform(mass.blocks, CRS("+proj=utm +zone=20 ellps=WGS84"))

# determine the blocks that are covered by the 0.5 mile buffer
mass.blocks.centroid <- st_centroid(mass.blocks, byid = TRUE)

overlap.blk <- mass.blocks[!is.na(st_intersects(mass.blocks.centroid,utm.buffer)),]


######## DETERMINING CENSUS TRACTS TO SELECT ########
# change population variables to numeric (original data type: character)
# mass.blocks@data$B01003_001 <- as.numeric(mass.blocks@data$B01003_001)
# mass.ct@data$B01003_001 <- as.numeric(mass.ct@data$B01003_001)



overlap.ct <- mass.ct[!is.na(st_intersects(mass.ct,utm.buffer)),]

overlap.ct

overlap.ct <- overlap.ct[overlap.ct@data$GEOID %in% unique(overlap.blk@data$GEOID),]

# determine the blocks in tract that are within the buffer zone and sum the population by tract
blks.in.tract <- c()

for (i in 1:length(unique(overlap.blk$GEOID))) {
  blks.in.tract[i] <- sum(overlap.blk@data[overlap.blk@data$GEOID==overlap.ct$GEOID[i],]$value)
}

t <- mass.ct[mass.ct$GEOID %in% overlap.ct$GEOID,]


# determine block group of development
overlap.bg <- mass.bg[!is.na(over(mass.bg,utm)),]

# study area 1 = 50%+ of population within 0.5 mile radius
sum.df.1 <- data.frame(overlap.ct$GEOID, blks.in.tract, t$value, blks.in.tract >= 0.5*t$value)
colnames(sum.df.1) <- c("tract", "pop.blks.in.tract", "totpop", "majority.in.buffer")
sa1 <- sum.df.1$tract[sum.df.1$majority.in.buffer == TRUE]
sa1 <- as.numeric(as.character(sa1))
sa1_name <- paste(addresses$study.area, 1, sep = " ") 
sa1_bg <- overlap.bg@data$GEOID
sa1_muni <- addresses$municipality

sa1

sa1_name

sa1_bg

sa1_muni

# study area 2 = 40%+ of population within 0.5 mile radius
# sum.df.2 <- data.frame(overlap.ct$GEOID20, blks.in.tract, t$B01003_001, blks.in.tract > 0.4*t$B01003_001)
# colnames(sum.df.2) <- c("tract", "pop.blks.in.tract", "totpop", "majority.in.buffer")
# sa2 <- sum.df.2$tract[sum.df.2$majority.in.buffer == TRUE]
# sa2 <- as.numeric(as.character(sa2))
# sa2_name <- paste(addresses$study.area, 2, sep = " ") 
# sa2_bg <- overlap.bg@data$GEOID20
# sa2_muni <- addresses$municipality

######## MAPPING ########
# Create a natural jenks shading scheme
# jenks <- classIntervals(mass.blocks@data$B01003_001[mass.blocks$REALTOWN == addresses$municipality], n=5, style="jenks")
# shades <- shading(jenks$brks, cols = brewer.pal(5, "Greys"))
# 
# localdir <- "K:/DataServices/Projects/Current_Projects/Healthy_Neighborhoods_Equity_Funds"
# setwd(localdir)
# 
# # plot study area 1
# pdf(paste0("sa1_", tolower(gsub(" ", "", addresses$study.area, fixed = TRUE)), ".pdf"), width = 8.5, height = 11)
# 
# plot(mass.ct[mass.ct$GEOID20 %in% sum.df.1$tract[sum.df.1$majority.in.buffer == TRUE],],
#      border = NA)
# 
# plot(mass.blocks[mass.blocks$GEOID20 %in% overlap.blk$GEOID20,],
#      border = "grey47",
#      add=TRUE)
# 
# choropleth(mass.blocks[mass.blocks$REALTOWN == addresses$municipality,], 
#            mass.blocks@data$B01003_001[mass.blocks$REALTOWN == addresses$municipality],
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
# plot(mass.ct[mass.ct$GEOID20 %in% sum.df.1$tract[sum.df.1$majority.in.buffer == TRUE],],
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
# plot(mass.ct[mass.ct$GEOID20 %in% sum.df.2$tract[sum.df.2$majority.in.buffer == TRUE],],
#      border = NA)
# 
# plot(mass.blocks[mass.blocks$GEOID20 %in% overlap.blk$GEOID20,],
#      border = "grey47",
#      add=TRUE)
# 
# choropleth(mass.blocks[mass.blocks$REALTOWN == addresses$municipality,], 
#            mass.blocks@data$B01003_001[mass.blocks$REALTOWN == addresses$municipality],
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
# plot(mass.ct[mass.ct$GEOID20 %in% sum.df.2$tract[sum.df.2$majority.in.buffer == TRUE],],
#      border = "darkgoldenrod2",
#      lwd = 3,
#      add=TRUE)
# 
# plot(mass.towns[mass.towns$TOWN==addresses$municipality,],
#      border = "black",
#      add = TRUE)
# 
# dev.off()
