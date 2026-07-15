-- sql/extract_ergoespirometry.sql
-- Extrae una fila por GXTest con sus binarios y predicciones de la visita.

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
    pv.Signed,
    pv.SignedDateTime,

    gx.GXTestID,
    gx.GXTestStartTime,
    gx.GXTestEndTime,
    gx.GXTestExProtocolName,
    gx.GXTestScriptName,
    gx.GXTestScriptType,
    gx.GXTestBorgScale,
    gx.GXTestBPFreq,
    gx.GXTestExternalDeadspace,
    gx.StartExerciseTime,
    gx.StartRecoveryTime,
    gx.ATElapsedTime,
    gx.RCElapsedTime,
    gx.VO2MaxElapsedTime,
    gx.GXTestMinRER,
    gx.GXTestMaxRER,
    gx.GXTestMinVO2,
    gx.GXTestMinVCO2,
    gx.GXTestRawData,
    gx.ManuallyEnteredData,

    pred.GXPredictedID,
    pred.VE_BTPS,
    pred.BP_systolic,
    pred.VO2Bike_kg,
    pred.VO2Treadmill_kg,
    pred.HR AS PredictedHR,
    pred.VO2HRBike,
    pred.VO2HRTreadmill,
    pred.METSBike,
    pred.METSTreadmill,
    pred.RatePresPd,
    pred.VO2Bike_mLmin,
    pred.VO2Treadmill_mLmin,
    pred.VCO2Bike,
    pred.VCO2Treadmill,
    pred.VEVO2Bike,
    pred.VEVO2Treadmill,
    pred.VEVCO2Bike,
    pred.VEVCO2Treadmill,
    pred.Speed_KPH,
    pred.BikeWatts,
    pred.TreadmillWatts,
    pred.VE_NormPred,
    pred.VO2VE,
    pred.VCO2VE,
    pred.Bike_VO2IBWkg,
    pred.TMill_VO2IBWkg,
    pred.IdealBodyWeight

FROM dbo.GXTest AS gx

INNER JOIN dbo.PatVisit AS pv
    ON gx.PatVisitID = pv.PatVisitID

INNER JOIN dbo.Patient AS p
    ON pv.PatientGUID = p.PatientGUID

LEFT JOIN dbo.GXPredicted AS pred
    ON gx.PatVisitID = pred.PatVisitID

WHERE pv.VisitDateTime >= ?
  AND pv.VisitDateTime < ?

ORDER BY
    pv.VisitDateTime,
    pv.PatVisitID,
    gx.GXTestID;
