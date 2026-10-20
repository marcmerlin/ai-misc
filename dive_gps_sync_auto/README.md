Copied from https://marc.merlins.org/perso/diving/post_2026-10-18_Subsurface-GPS-Locations-Adding-From-GPX-Tracks-and-Waypoints.html

And you can check out my 49572 pictures and blog entries from 77 trips and 994 dives over 23 years as of this writing, you can find them here: https://marc.merlins.org/perso/diving/

After my last dive trip in French Polynesia, I was 6 dives short of 1000, but I had hundreds of dives in subsurface that didn't have GPS locations. My Dive computers (all 3 of them) do not log GPS data, and ever since the old subsurface android client that would log GPS locations and sync them against dives in the cloud after the fact, went end of life, none of my dives had GPS locations anymore.
And yet, I had 40+ GPS GPX files from my garmin that is always running on my dive trips, so I knew just like I used to geotag my pictures with GPX files and date/time matching from the pictures EXIF data, the same was clearly possible with Subsurface, but when I asked, no one had done it (and to be fair, it's tedious code to write by hand).
Also, Subsurface does not keep track of timezones, but stores times in local time as this is what dive computers do (without storing timezone along with it, and even cameras took maybe more than 10 years before finally storing timezone data in the EXIF tag...).

So my goal was to just have most of my dives have a location on the map, I just wanted those little flags all over the world:
<img width="1478" height="1123" alt="image" src="https://github.com/user-attachments/assets/1dfb93a8-f8e5-4b38-a28e-17c5912b3ce6" />

Now, I need to state right now, I didn't really care if the location was exact, hell if it's off by 12h and maybe 100km from the actual site for a few dives because the time was wrong on my dive computer, or the GPS info wasn't present around that hour, I'm still happy to have the little flag in the general location where the dive happened. If this is not good for you, you can play with the --max-hours flag, and hope you never forgot to change the time in your dive computer each time you went to a different timezone (I know a few times, I did a few dives with the wrong time from the last part of the world I used to be in, but as I just said, I'm fine with close enough, as in just the correct side of the world :)

Ok, so now let's talk about the code. We now live in the word of AI, gemini came to the rescue (used in pro high mode). I did use my brain for a single good idea that we didn't know timezones for the times in subsurface, but we could use the GPS locations and with a timezone database (timezonefinder python module in pip), and convert UTC times in the GPS file to local times for each location, which will happily match with the local time in subsurface. For the rest, I spent about 1h with gemini to have it figure out the somewhat non obvious dive location and global site location meanings of the subversion ssrf files, and within 1h, got the end result below.

So no, I didn't write the code, all I had to do is make symlinks to all my GPX files that contained dive locations over the last 15 years, and run the code (did that a few times with testing revisions of the code until I was happy wit the end result)

```
sauron:~/gps/data/diving$ l *.gpx | head -3
lrwxrwxrwx 1 merlin merlin 27 Oct 18 22:06 20080202_Fiji_Diving.gpx -> ../20080202_Fiji_Diving.gpx
lrwxrwxrwx 1 merlin merlin 33 Oct 18 22:09 20090811_Hawaii_Maui_Kauai.gpx -> ../20090811_Hawaii_Maui_Kauai.gpx
lrwxrwxrwx 1 merlin merlin 32 Oct 18 22:13 20100529_Belize_Aggressor.gpx -> ../20100529_Belize_Aggressor.gpx*
sauron:~/gps/data/diving$ dive_gps_sync_auto ~/marc.ssrf --gpx "*.gpx" --max-hours 12
Loading GPX files from pattern: *.gpx
Initializing offline timezone engine...
Calculated local timezones for 1398219 GPS points.

Dive #275 (Belise Aggressor III - Day 3) matched to Local GPX time 2010-05-31 07:09:36 [diff: 0:02:36]. Assigning GPS: 17.2137829 -87.6143720
Dive #276 (Belise Aggressor III) matched to Local GPX time 2010-05-31 10:34:57 [diff: 0:02:03]. Assigning GPS: 17.2134649 -87.6143339
Dive #279 (Belise Aggressor III - Day 4) matched to Local GPX time 2010-06-01 04:35:19 [diff: 0:04:41]. Assigning GPS: 17.2036230 -87.5416109
Dive #283 (Belise Aggressor III - Day 5) matched to Local GPX time 2010-06-02 04:33:53 [diff: 0:01:53]. Assigning GPS: 17.2156519 -87.6123730
(...)
Dive #967 (Rangiroa Tiputa Pass) matched to Local GPX time 2026-09-30 14:44:48 [diff: 0:00:02]. Assigning GPS: -14.969145153 -147.623316413
Dive #981 (Fakarava South Pass) matched to Local GPX time 2026-10-06 09:10:00 [diff: 0:00:04]. Assigning GPS: -16.518651769 -145.460582804
Dive #983 (Fakarava North Pass) matched to Local GPX time 2026-10-07 08:16:54 [diff: 0:00:08]. Assigning GPS: -16.077915374 -145.713441521

Successfully auto-matched and added GPS data to 339 dive(s).

--- Dives Still Missing GPS Tags ---
Dive #296: Heron Island
Dive #297: Heron Island
Dive #298: Heron Island
Dive #328: San Diego Marissa Charters
Dive #329: San Diego Marissa Charters
Dive #330: San Diego Marissa Charters
Dive #331: San Diego Marissa Charters
Dive #332: San Diego Marissa Charters
Dive #333: San Diego Marissa Charters
Dive #458: Alore 11-1: Amet Knoll
Dive #459: Alore 11-2: Pombo Island
Dive #716: Dubai Aquarium


--- Unique Locations Missing GPS ---
- Alore 11-1: Amet Knoll
- Alore 11-2: Pombo Island
- Dubai Aquarium
- Heron Island
- San Diego Marissa Charters


Total unique missing locations: 5


=================================================
VERSION: v7
OUTPUT_FILE: updated_divelog.ssrf
=================================================
sauron:~/gps/data/diving$ 
```
