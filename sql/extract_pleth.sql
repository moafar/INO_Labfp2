-- sql/extract_pleth.sql
-- Extrae pacientes, visitas y resultados Pleth desde SQL Server.

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

    pl.PlethDataID,
    pl.EffortTypeID,
    et.EffortTypeDesc,
    pl.EffortTime,
    pl.EffortArtificial,
    pl.EffortManual,
    pl.PlethRAWSelected,
    pl.PlethTGVSelected,
    pl.PFProtocolStageIndex,
    -- PLETH_COLUMNS

FROM dbo.Patient AS p

INNER JOIN dbo.PatVisit AS pv
    ON p.PatientGUID = pv.PatientGUID

INNER JOIN dbo.PlethData AS pl
    ON pv.PatVisitID = pl.PatVisitID

INNER JOIN (
    SELECT DISTINCT PatVisitID
    FROM dbo.PlethData
    WHERE EffortTypeID = 0
) AS visitas_con_maniobras
    ON visitas_con_maniobras.PatVisitID = pv.PatVisitID

LEFT JOIN dbo.EffortType AS et
    ON pl.EffortTypeID = et.EffortTypeID

WHERE pv.PlethTest = 1
  AND pv.VisitDateTime >= ?
  AND pv.VisitDateTime < ?

ORDER BY
    pv.VisitDateTime,
    pv.PatVisitID,
    pl.PlethDataID;
