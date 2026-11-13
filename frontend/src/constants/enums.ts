export const roles=["admin","analyst","viewer"] as const;
export const runStatuses=["queued","running","completed","failed"] as const;
export const meterStatuses=["running","stopped"] as const;
export const sourceModes=["hourly","cumulative"] as const;
export const sourceModeLabels:Record<string,string>={hourly:"小时电量",cumulative:"累计示数"};
export const exclusionLabels:Record<string,string>={stopped:"停机",zero_output:"零产量",missing_measurement:"缺测",first_baseline:"首条基准",rebased:"缺测后重建基准",rollback:"示数回退",hour_gap:"跨小时缺口"};
