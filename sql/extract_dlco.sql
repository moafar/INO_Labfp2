-- sql/extract_dlco.sql
-- Extrae pacientes, visitas y resultados de DLCO desde SQL Server.

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

    dl.DLCODataID,
    dl.EffortTypeID,
    et.EffortTypeDesc,
    dl.EffortTime,
    dl.EffortArtificial,
    dl.EffortManual,
    dl.PFProtocolStageIndex,
    dl.EffortSelected,
    -- DLCO_COLUMNS

FROM dbo.Patient AS p

INNER JOIN dbo.PatVisit AS pv
    ON p.PatientGUID = pv.PatientGUID

INNER JOIN dbo.DLCOData AS dl
    ON pv.PatVisitID = dl.PatVisitID

INNER JOIN (
    SELECT DISTINCT PatVisitID
    FROM dbo.DLCOData
    WHERE EffortTypeID = 0
) AS visitas_con_maniobras
    ON visitas_con_maniobras.PatVisitID = pv.PatVisitID

LEFT JOIN dbo.EffortType AS et
    ON dl.EffortTypeID = et.EffortTypeID

WHERE pv.VisitDateTime >= ?
  AND pv.VisitDateTime < ?

ORDER BY
    pv.VisitDateTime,
    pv.PatVisitID,
    dl.DLCODataID;
