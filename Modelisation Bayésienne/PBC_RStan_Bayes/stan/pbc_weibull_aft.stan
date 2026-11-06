data {
  int<lower=1> N;
  int<lower=1> K;
  matrix[N, K] X;
  vector<lower=0>[N] time_days;
  array[N] int<lower=0, upper=1> event;
}

parameters {
  real alpha;
  vector[K] beta;
  real<lower=0> shape;
}

model {
  vector[N] log_scale = alpha + X * beta;

  alpha ~ normal(log(2000), 1.5);
  beta ~ normal(0, 1);
  shape ~ lognormal(log(1.5), 0.5);

  for (n in 1:N) {
    if (event[n] == 1) {
      target += weibull_lpdf(time_days[n] | shape, exp(log_scale[n]));
    } else {
      target += weibull_lccdf(time_days[n] | shape, exp(log_scale[n]));
    }
  }
}

generated quantities {
  real time_ratio_dpenicillamine = exp(beta[4]);
}
