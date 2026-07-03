-- sql/extract_fvl.sql
-- Extrae pacientes, visitas y resultados de espirometría desde SQL Server.

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

    fv.FVLDataID,
    fv.EffortTypeID,
    et.EffortTypeDesc,
    fv.EffortTime,
    fv.EffortArtificial,
    fv.EffortManual,
    fv.PFProtocolStageIndex,
    fv.EffortSelected,
    -- FVL_COLUMNS

FROM dbo.Patient AS p

INNER JOIN dbo.PatVisit AS pv
    ON p.PatientGUID = pv.PatientGUID

INNER JOIN dbo.FVLData AS fv
    ON pv.PatVisitID = fv.PatVisitID

LEFT JOIN dbo.EffortType AS et
    ON fv.EffortTypeID = et.EffortTypeID

WHERE pv.VisitDateTime >= ?
  AND pv.VisitDateTime < ?
  AND pv.FVLTest = 1

ORDER BY
    pv.VisitDateTime,
    pv.PatVisitID,
    fv.FVLDataID;