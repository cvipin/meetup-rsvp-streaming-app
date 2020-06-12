CREATE DATABASE meetup;

USE meetup;

CREATE TABLE MeetupRSVP
(
  GroupName varchar(1000),
  GroupCountry varchar(200),
  GroupState varchar(200),
  GroupCity varchar(200),
  GroupLatitude  double,
  GroupLongitude double,
  RSVPResponse  varchar(10),
  ResponseCount int,
  EpochId int
);

-- Select query for realtime reporting
use meetup;

SELECT m1.GroupName, m1.RSVPResponse, SUM(ResponseCount) ResponseCount
FROM meetup.MeetupRSVP m1
JOIN (
  SELECT GroupName, MAX(EpochId) EpochId
  FROM meetup.MeetupRSVP
  GROUP BY GroupName
) m2 ON m1.GroupName = m2.GroupName AND m1.EpochId = m2.EpochId
GROUP BY m1.GroupName, m1.RSVPResponse
ORDER BY ResponseCount DESC
LIMIT 10;
