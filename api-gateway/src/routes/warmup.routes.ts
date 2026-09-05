import { Router } from "express";

import {
  getWarmupStatus,
  startWarmup,
} from "../controllers/warmup.controller";

const router = Router();

router.post("/api/warmup", startWarmup);
router.get("/api/warmup", getWarmupStatus);

export default router;
