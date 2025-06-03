import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict # Not strictly used in this endpoint but good for general API dev

from backend.app.services.ml_prediction_service import MLPredictionService
from backend.app.models.ml_prediction_models import (
    MomentumSustainabilityInputFeatures,
    MomentumSustainabilityOutput,
    BreakoutViabilityInputFeatures,
    BreakoutViabilityOutput,
    AbsorptionEventInputFeatures,  # Added
    AbsorptionOutcomeOutput        # Added
)
# from backend.app.core.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/predict/momentum_sustainability",
    response_model=MomentumSustainabilityOutput,
    summary="Predict Momentum Sustainability Score",
    description="Receives bar/event features and returns a score indicating the sustainability of observed momentum."
)
async def predict_momentum_sustainability_endpoint(
    features: MomentumSustainabilityInputFeatures,
    ml_service: MLPredictionService = Depends(MLPredictionService) # FastAPI will instantiate or reuse service
    # current_user: User = Depends(get_current_user) # Optional: if endpoint requires authentication
):
    """
    Endpoint to predict momentum sustainability.
    - **features**: Input features for the model as defined in `MomentumSustainabilityInputFeatures`.
    """
    logger.info(f"Received request for momentum sustainability prediction: {features.bar_timestamp}, Delta: {features.bar_delta}")
    try:
        # The service method is async, so await it
        prediction_output = await ml_service.predict_momentum_sustainability(features)
        logger.info(f"Prediction result for {features.bar_timestamp}: Score={prediction_output.sustainability_score}")
        return prediction_output
    except ValueError as ve: # Catch specific validation or data errors if service raises them
        logger.warning(f"Validation error during momentum sustainability prediction: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error during momentum sustainability prediction: {e}", exc_info=True)
        # Avoid leaking detailed internal errors to client; log them instead
        raise HTTPException(status_code=500, detail="An internal error occurred during prediction.")


@router.post(
    "/predict/breakout_viability",
    response_model=BreakoutViabilityOutput,
    summary="Predict Breakout Viability",
    description="Receives features related to a breakout attempt and returns probabilities of true vs. false breakout."
)
async def predict_breakout_viability_endpoint(
    features: BreakoutViabilityInputFeatures,
    ml_service: MLPredictionService = Depends(MLPredictionService)
    # current_user: User = Depends(get_current_user) # Optional auth
):
    """
    Endpoint to predict breakout viability.
    - **features**: Input features for the model as defined in `BreakoutViabilityInputFeatures`.
    """
    logger.info(f"Received request for breakout viability prediction: Price Level={features.breakout_price_level}, Bar Timestamp={features.bar_timestamp_breakout_attempt}")
    try:
        prediction_output = await ml_service.predict_breakout_viability(features)
        logger.info(f"Breakout viability prediction for event at {features.bar_timestamp_breakout_attempt}, Level: {features.breakout_price_level}: ProbTrue={prediction_output.probability_true_breakout:.2f}")
        return prediction_output
    except ValueError as ve:
        logger.warning(f"Validation error during breakout viability prediction: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error during breakout viability prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during breakout viability prediction.")


@router.post(
    "/predict/absorption_outcome",
    response_model=AbsorptionOutcomeOutput,
    summary="Predict Absorption Event Outcome",
    description="Receives features of an absorption event and predicts the likely outcome (Reversal, Continuation, Consolidation)."
)
async def predict_absorption_outcome_endpoint(
    features: AbsorptionEventInputFeatures,
    ml_service: MLPredictionService = Depends(MLPredictionService)
    # current_user: User = Depends(get_current_user) # Optional auth
):
    """
    Endpoint to predict the outcome of an absorption event.
    - **features**: Input features for the model as defined in `AbsorptionEventInputFeatures`.
    """
    logger.info(f"Received request for absorption outcome prediction: Price Level={features.absorption_price_level}, Event Timestamp={features.event_timestamp}")
    try:
        prediction_output = await ml_service.predict_absorption_outcome(features)
        logger.info(
            f"Absorption outcome prediction for event at {features.event_timestamp}, Level: {features.absorption_price_level}: "
            f"Predicted: {prediction_output.predicted_outcome_label} "
            f"(Reversal: {prediction_output.probability_reversal:.2f}, "
            f"Continuation: {prediction_output.probability_continuation:.2f}, "
            f"Consolidation: {prediction_output.probability_consolidation:.2f})"
        )
        return prediction_output
    except ValueError as ve:
        logger.warning(f"Validation error during absorption outcome prediction: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error during absorption outcome prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during absorption outcome prediction.")
