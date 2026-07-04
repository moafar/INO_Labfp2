-- sql/extract_methacholine.sql
-- Extrae etapas de broncoprovocación con metacolina desde SQL Server.

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
    pv.PFProtocolGUID,
    pv.LastPFProtocolStageIndex,
    pv.TestingStage,

    pp.PFProtocolName,
    pp.ChallengeAgentID,
    ca.ChallengeAgentName,
    ca.ChallengeAgentType,

    ps.PFProtocolStageIndex,
    ps.PFProtocolStageLabel,
    ps.PFProtocolStageConcentration,
    ps.PFProtocolStageDeliveredDose,
    ps.PFProtocolStageComment,

    fv.FVLDataID,
    fv.EffortTypeID,
    et.EffortTypeDesc,
    fv.EffortTime,
    fv.EffortArtificial,
    fv.EffortManual,
    fv.PFProtocolStageIndex AS FVLProtocolStageIndex,
    fv.EffortSelected,

    fv.FVC,
    fv.FEV1,
    fv.FEV1FVC,
    fv.FEF2575,
    fv.PEF,
    fv.FVLATSCodes,
    fv.TestGradeATS,
    fv.TestGradeNLHEP

FROM dbo.Patient AS p

INNER JOIN dbo.PatVisit AS pv
    ON p.PatientGUID = pv.PatientGUID

INNER JOIN dbo.FVLData AS fv
    ON pv.PatVisitID = fv.PatVisitID

INNER JOIN dbo.PFProtocol AS pp
    ON pv.PFProtocolGUID = pp.PFProtocolGUID

INNER JOIN dbo.ChallengeAgent AS ca
    ON pp.ChallengeAgentID = ca.ChallengeAgentID

LEFT JOIN dbo.PFProtocolStage AS ps
    ON ps.PFProtocolGUID = pp.PFProtocolGUID
   AND ps.PFProtocolStageIndex = fv.PFProtocolStageIndex

LEFT JOIN dbo.EffortType AS et
    ON fv.EffortTypeID = et.EffortTypeID

WHERE pv.VisitDateTime >= ?
  AND pv.VisitDateTime < ?
  AND fv.EffortTypeID IN (2, 8, 3)
  AND ca.ChallengeAgentName = 'Methacholine'
  AND pp.PFProtocolName = 'TEST DE METACOLINA'

ORDER BY
    pv.VisitDateTime,
    pv.PatVisitID,
    fv.PFProtocolStageIndex,
    fv.FVLDataID;
