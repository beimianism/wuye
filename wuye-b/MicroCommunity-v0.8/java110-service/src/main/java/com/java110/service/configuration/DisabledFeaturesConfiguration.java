package com.java110.service.configuration;

import com.java110.utils.config.DisabledFeatures;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.Ordered;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

/** Apply the same scope to direct Java requests and requests through the Web proxy. */
@Configuration
public class DisabledFeaturesConfiguration {
    @Bean
    public FilterRegistrationBean<OncePerRequestFilter> disabledFeaturesFilter() {
        FilterRegistrationBean<OncePerRequestFilter> registration = new FilterRegistrationBean<>();
        registration.setOrder(Ordered.HIGHEST_PRECEDENCE + 10);
        registration.addUrlPatterns("/*");
        registration.setFilter(new OncePerRequestFilter() {
            @Override
            protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                            FilterChain chain) throws ServletException, IOException {
                String uri = request.getRequestURI().substring(request.getContextPath().length());
                if (DisabledFeatures.isDisabledRequest(uri)) {
                    response.setStatus(HttpServletResponse.SC_GONE);
                    response.setContentType("application/json;charset=UTF-8");
                    response.getWriter().write("{\"code\":410,\"msg\":\"该功能已停用\"}");
                    return;
                }
                chain.doFilter(request, response);
            }
        });
        return registration;
    }
}
