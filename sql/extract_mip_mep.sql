-- sql/extract_mip_mep.sql
-- Extrae pacientes, visitas y resultados basales válidos de MIP/MEP desde SQL Server.

SELECT
    p.PatientGUID,
    p.PatientIDNum,
    p.PatientLastName,
    p.PatientFirstName,
    p.PatientMidName,
    p.Birthday,
    p.SexListID,
    p.RaceListID,

    pv.PatVisitID,
    pv.PatVisitGUID,
    pv.VisitDateTime,
    pv.Age,
    pv.Weight,
    pv.Height,
    pv.BMI,
    pv.PredSetName,
    pv.Diagnosis,
    pv.Comments,
    pv.PostComm,
    pv.Signed,
    pv.SignedDateTime,
    pv.MipMepTest,

    mp.MipDataID,
    mp.EffortTypeID,
    et.EffortTypeDesc,
    mp.EffortTime,
    mp.EffortArtificial,
    mp.EffortManual,
    mp.EffortSelected,
    mp.PFProtocolStageIndex,
    mp.MIP,
    mp.MEP

FROM dbo.Patient AS p

INNER JOIN dbo.PatVisit AS pv
    ON p.PatientGUID = pv.PatientGUID

INNER JOIN dbo.MipData AS mp
    ON pv.PatVisitID = mp.PatVisitID

LEFT JOIN dbo.EffortType AS et
    ON mp.EffortTypeID = et.EffortTypeID

WHERE pv.VisitDateTime >= ?
  AND pv.VisitDateTime < ?
  AND mp.EffortTypeID = 2
  AND (
      mp.MIP <> 0
      OR mp.MEP <> 0
  )

ORDER BY
    pv.VisitDateTime,
    pv.PatVisitID,
    mp.MipDataID;